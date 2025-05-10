from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship, declarative_base, validates
from sqlalchemy import Enum as SQLAlchemyEnum
from datetime import datetime, date
from enum import Enum
import re

Base = declarative_base()

class Paciente(Base):
    """Modelo de paciente com validações integradas para dados clínicos.
    
    Attributes:
        id: Chave primária automática
        nome: Nome completo (100 caracteres, obrigatório)
        cpf: CPF único (11 dígitos, validado)
        data_nascimento: Data no passado (obrigatório)
        telefone: Número com DDD (15 dígitos, validado)
        historico_clinico: Texto livre opcional
        alergias: Texto livre opcional
        consentimento_lgpd: Booleano obrigatório
        data_cadastro: Timestamp automático
    
    Example:
        Paciente(
            nome="João Silva",
            cpf="12345678909",
            data_nascimento="2000-01-01",
            telefone="11999999999",
            consentimento_lgpd=True
        )
    """
    __tablename__ = 'pacientes'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    telefone = Column(String(15), nullable=False)
    historico_clinico = Column(Text)
    alergias = Column(Text)
    consentimento_lgpd = Column(Boolean, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)

    @validates('data_nascimento')
    def valida_data_nascimento(self, key, value):
        if isinstance(value, str):
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError("Formato de data inválido. Use YYYY-MM-DD")
                
        if not isinstance(value, date):
            raise TypeError("Data deve ser um objeto date ou string ISO")
            
        if value > date.today():
            raise ValueError("Data de nascimento não pode ser futura")
            
        return value

    @validates('telefone')
    def valida_telefone(self, key, value):
        if not re.match(r'^(\(\d{2}\)\s?)?(\d{4,5}-?\d{4})$', value):
            raise ValueError("Telefone inválido. Exemplos válidos: (11) 99999-9999 ou 11999999999")
        return value

    __table_args__ = (
        CheckConstraint(
            "LENGTH(cpf) = 11 AND cpf NOT GLOB '[^0-9]*'", 
            name='formato_cpf_valido'
        ),
    )

class Especialidade(str, Enum):
    MEDICO = 'médico'
    ENFERMEIRO = 'enfermeiro'
    OUTRO = 'outro'

class Profissional(Base):
    """Modelo para profissionais de saúde com autenticação.
    
    Validações:
        - CPF único e válido
        - Senha com hash bcrypt
        - Especialidade pré-definida
    """
    __tablename__ = 'profissionais'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    especialidade = Column(SQLAlchemyEnum(Especialidade, native_enum=False), nullable=False)
    hash_senha = Column(String(255), nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)

    @validates('cpf')
    def valida_cpf(self, key, value):
        if len(value) != 11 or not value.isdigit():
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return value

class StatusAgendamento(str, Enum):
    AGENDADO = 'agendado'
    REMARCADO = 'remarcado'
    CANCELADO = 'cancelado'

class Agendamento(Base):
    """Modelo para gestão de agendamentos com restrições temporais.
    
    Constraints:
        - Horário de término após horário inicial
        - Status dentro dos valores permitidos
    """
    __tablename__ = 'agendamentos'
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'), nullable=False)
    profissional_id = Column(Integer, ForeignKey('profissionais.id'), nullable=False)
    inicio = Column(DateTime, nullable=False)
    fim = Column(DateTime, nullable=False)
    status = Column(SQLAlchemyEnum(StatusAgendamento, native_enum=False), default=StatusAgendamento.AGENDADO)
    tipo_consulta = Column(String(50), default='presencial')

    paciente = relationship('Paciente', backref='agendamentos')
    profissional = relationship('Profissional', backref='agendamentos')

    @validates('fim')
    def valida_horario(self, key, value):
        if self.inicio and value <= self.inicio:
            raise ValueError("Horário de término deve ser após o inicial")
        return value

class LogAuditoria(Base):
    """Registro de auditoria para ações críticas no sistema."""
    __tablename__ = 'logs_auditoria'
    
    id = Column(Integer, primary_key=True)
    acao = Column(String(50), nullable=False)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String(50), nullable=False)
    detalhes = Column(String(500))

    def __init__(self, acao: str, usuario: str, detalhes: str):
        self.acao = acao
        self.usuario = usuario
        self.detalhes = detalhes

    @validates('acao')
    def valida_acao(self, key, value):
        acoes_permitidas = ['CADASTRO', 'ATUALIZACAO', 'EXCLUSAO', 'LOGIN', 'OUTRO']
        if value.split('_')[0] not in acoes_permitidas:
            raise ValueError("Tipo de ação não permitida")
        return value