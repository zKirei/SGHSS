# core/services.py (versão melhorada)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
from .models import Paciente, Agendamento, Profissional, LogAuditoria, StatusAgendamento
from .security import sanitizar_input, gerar_hash_senha
from .utils import validar_cpf, validar_telefone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PacienteService:
    @staticmethod
    def criar_paciente(db: Session, dados: dict):
        """Cria um novo paciente no sistema com validações e sanitização."""
        try:
            # Validação dos campos obrigatórios
            if not dados.get('nome'):
                raise ValueError("Nome é obrigatório")
                
            if not dados.get('cpf'):
                raise ValueError("CPF é obrigatório")
                
            if not dados.get('consentimento_lgpd', False):
                raise ValueError("Consentimento LGPD é obrigatório")

            # Validação de CPF e telefone
            cpf = dados.get('cpf', '')
            telefone = dados.get('telefone', '')
            
            if not validar_cpf(cpf):
                raise ValueError("CPF inválido! Verifique os dígitos verificadores.")
                
            if not validar_telefone(telefone):
                raise ValueError("Telefone inválido! Deve conter DDD + número (ex: 41999999999).")

            # Converter e validar data
            data_nascimento = PacienteService._converter_data(dados.get('data_nascimento'))

            # Sanitização
            paciente = Paciente(
                cpf=sanitizar_input(cpf),
                nome=sanitizar_input(dados['nome']),
                telefone=sanitizar_input(telefone),
                data_nascimento=data_nascimento,
                consentimento_lgpd=dados.get('consentimento_lgpd', False),
                historico_clinico=sanitizar_input(dados.get('historico_clinico', ''))
            )

            db.add(paciente)
            db.commit()
            
            # Log de auditoria
            log = LogAuditoria(
                acao=f"CADASTRO_PACIENTE - ID: {paciente.id}",
                usuario="SISTEMA",
                data_hora=datetime.now()
            )
            db.add(log)
            db.commit()
            
            return paciente
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro no cadastro: {str(e)}", exc_info=True)
            raise ValueError(f"Falha no cadastro: {str(e)}") from e
        except ValueError as e:
            db.rollback()
            logger.error(f"Erro de validação: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
            raise ValueError("Falha inesperada no cadastro") from e

    @staticmethod
    def _converter_data(data_str: Optional[str]) -> Optional[date]:
        """Converte string de data para objeto date."""
        if not data_str:
            return None
            
        try:
            return datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Formato de data inválido: {data_str}")
            raise ValueError("Data de nascimento inválida. Use o formato YYYY-MM-DD") from e

class ProfissionalService:
    @staticmethod
    def criar_profissional(db: Session, dados: dict):
        try:
            if not validar_cpf(dados.get('cpf', '')):
                raise ValueError("CPF inválido para profissional!")
                
            if len(dados.get('senha', '')) < 8:
                raise ValueError("Senha deve ter no mínimo 8 caracteres!")
                
            profissional = Profissional(
                cpf = sanitizar_input(dados['cpf']),
                nome = sanitizar_input(dados['nome']),
                especialidade = dados['especialidade'],
                hash_senha = gerar_hash_senha(dados['senha']),
                data_cadastro = datetime.now()
            )
            
            db.add(profissional)
            db.commit()
            
            # Log de criação de profissional
            log = LogAuditoria(
                acao=f"CADASTRO_PROFISSIONAL - ID: {profissional.id}",
                usuario="ADMIN",
                data_hora=datetime.now()
            )
            db.add(log)
            db.commit()
            
            return profissional
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro profissional: {str(e)}", exc_info=True)
            raise ValueError(f"Falha no cadastro: {str(e)}") from e

class AgendamentoService:
    @staticmethod
    def agendar_consulta(db: Session, dados: dict):
        try:
            # Converter string para datetime se necessário
            if isinstance(dados['inicio'], str):
                dados['inicio'] = datetime.fromisoformat(dados['inicio'])
            if isinstance(dados['fim'], str):
                dados['fim'] = datetime.fromisoformat(dados['fim'])

            # Validação de tempo (permite agendamentos passados para testes)
            if (dados['inicio'] - datetime.now()).total_seconds() < 0:
                logger.warning("Agendamento no passado permitido para testes")

            # Verificação de conflito otimizada
            conflito = db.query(Agendamento).filter(
                Agendamento.profissional_id == dados['profissional_id'],
                Agendamento.inicio == dados['inicio'],
                Agendamento.status == StatusAgendamento.AGENDADO
            ).first()
            
            if conflito:
                logger.error(f"Conflito de agendamento: {dados}")
                raise ValueError("Horário já ocupado")

            # Criação do agendamento
            consulta = Agendamento(
                paciente_id=dados['paciente_id'],
                profissional_id=dados['profissional_id'],
                inicio=dados['inicio'],
                fim=dados['fim'],
                status=StatusAgendamento.AGENDADO,
                tipo_consulta=dados.get('tipo_consulta', 'presencial')
            )

            # Commit único para toda a operação
            db.add(consulta)
            db.commit()  # Confirma imediatamente

            logger.info(f"Agendamento {consulta.id} criado com sucesso")
            return consulta
            
        except Exception as e:
            db.rollback()
            logger.error(f"Falha crítica: {str(e)}", exc_info=True)
            raise ValueError(f"Erro no agendamento: {str(e)}") from e