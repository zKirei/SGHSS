from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, timedelta
from .models import Paciente, Agendamento, Profissional, LogAuditoria, StatusAgendamento
from .security import sanitizar_input, gerar_hash_senha, validar_cpf
from core.security import validar_cpf, validar_telefone
import logging
import re

logger = logging.getLogger(__name__)

class PacienteService:
    @staticmethod
    def criar_paciente(db: Session, dados: dict):
        """Cria paciente com validação reforçada do LGPD"""
        try:
            # Validação do consentimento LGPD (NOVA REGRA)
            if not dados.get('consentimento_lgpd', False):
                raise ValueError("Consentimento LGPD é obrigatório para cadastro")

            # Validação do telefone
            telefone = dados.get('telefone', '')
            if not re.match(r'^\(\d{2}\)\s?\d{4,5}-?\d{4}$', telefone):
                raise ValueError("Telefone inválido. Formato: (XX) XXXXX-XXXX")

            # Validação do CPF
            cpf_valido, msg = validar_cpf(dados['cpf'])
            if not cpf_valido:
                raise ValueError(f"CPF inválido: {msg}")

            # Validação da data de nascimento
            data_nascimento = datetime.strptime(dados['data_nascimento'], '%Y-%m-%d').date()
            if data_nascimento > date.today():
                raise ValueError("Data de nascimento futura")

            # Criação do paciente
            paciente = Paciente(
                cpf=re.sub(r'\D', '', dados['cpf']),
                nome=sanitizar_input(dados['nome']),
                telefone=telefone,
                data_nascimento=data_nascimento,
                consentimento_lgpd=dados['consentimento_lgpd']  # Já validado acima
            )

            db.add(paciente)
            db.commit()
            
            LogAuditoria.registrar(db, "CADASTRO_PACIENTE", "SISTEMA", f"Paciente {paciente.id} criado")
            return paciente

        except IntegrityError as e:
            db.rollback()
            if "UNIQUE constraint failed: pacientes.cpf" in str(e):
                raise ValueError("CPF já cadastrado") from e
            logger.error(f"Erro de integridade: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Erro crítico: {str(e)}", exc_info=True)
            raise

class AgendamentoService:
    @staticmethod
    def agendar_consulta(db: Session, dados: dict):
        """Agendamento com verificação de conflitos e validação temporal rigorosa"""
        try:
            inicio = datetime.fromisoformat(dados['inicio']) if isinstance(dados['inicio'], str) else dados['inicio']
            
            # Validação de horário passado
            if inicio < datetime.now() - timedelta(minutes=5):  # Tolerância de 5 minutos
                raise ValueError("Não é possível agendar no passado")

            # Verificação otimizada de conflitos
            conflito = db.query(Agendamento).filter(
                Agendamento.profissional_id == dados['profissional_id'],
                Agendamento.inicio == inicio,
                Agendamento.status == StatusAgendamento.AGENDADO
            ).first()
            
            if conflito:
                raise ValueError("Horário já ocupado por outro agendamento")

            consulta = Agendamento(
                paciente_id=dados['paciente_id'],
                profissional_id=dados['profissional_id'],
                inicio=inicio,
                fim=datetime.fromisoformat(dados['fim']) if isinstance(dados['fim'], str) else dados['fim'],
                status=StatusAgendamento.AGENDADO,
                tipo_consulta=sanitizar_input(dados.get('tipo_consulta', 'presencial'))
            )

            db.add(consulta)
            db.commit()
            
            LogAuditoria.registrar(db, "AGENDAMENTO", "SISTEMA", f"Consulta {consulta.id} agendada")
            return consulta

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro de banco: {str(e)}", exc_info=True)
            raise ValueError("Falha no agendamento") from e

class ProfissionalService:
    @staticmethod
    def criar_profissional(db: Session, dados: dict):
        """Cadastro de profissional com segurança reforçada"""
        try:
            if len(dados['senha']) < 12:
                raise ValueError("Senha deve ter pelo menos 12 caracteres")
                
            profissional = Profissional(
                cpf=re.sub(r'\D', '', dados['cpf']),
                nome=sanitizar_input(dados['nome']),
                especialidade=sanitizar_input(dados['especialidade']),
                hash_senha=gerar_hash_senha(dados['senha'])
            )
            
            db.add(profissional)
            db.commit()
            
            LogAuditoria.registrar(db, "CADASTRO", "ADMIN", f"Profissional {profissional.id} criado")
            return profissional

        except IntegrityError as e:
            db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("CPF já cadastrado") from e
            raise

class LogAuditoria:
    @staticmethod
    def registrar(db: Session, acao: str, usuario: str, detalhes: str):
        """Registro de logs com validação de ações permitidas"""
        acoes_validas = ["CADASTRO", "ATUALIZACAO", "EXCLUSAO", "LOGIN", "AGENDAMENTO"]
        if acao.split('_')[0] not in acoes_validas:
            raise ValueError(f"Ação {acao} não permitida")
            
        log = LogAuditoria(
            acao=acao,
            usuario=usuario,
            detalhes=detalhes[:500],  # Limite de caracteres
            data_hora=datetime.now()
        )
        db.add(log)
        db.commit()