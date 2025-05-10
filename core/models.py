from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base, validates
from sqlalchemy import Enum as SQLAlchemyEnum  # Importe o Enum do SQLAlchemy
from datetime import datetime, date
from enum import Enum

Base = declarative_base()

class Paciente(Base):
    """Modelo de paciente com dados pessoais e consentimento LGPD."""
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    telefone = Column(String(15), nullable=False)
    historico_clinico = Column(Text)
    alergias = Column(Text)
    consentimento_lgpd = Column(Boolean, default=False)
    data_cadastro = Column(DateTime, default=datetime.now)

    @validates('data_nascimento')
    def valida_data_nascimento(self, key, value):
        if isinstance(value, date) and value > date.today():
            raise ValueError("Data de nascimento não pode ser futura")

class Especialidade(str, Enum):  # Herda de str para compatibilidade
    MEDICO = 'médico'
    ENFERMEIRO = 'enfermeiro'
    OUTRO = 'outro'

class Profissional(Base):
    __tablename__ = 'profissionais'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    especialidade = Column(SQLAlchemyEnum(Especialidade), nullable=False)  # Use SQLAlchemyEnum
    hash_senha = Column(String(255), nullable=False)

class StatusAgendamento(str, Enum):  # Herda de str para compatibilidade
    AGENDADO = 'agendado'
    REMARCADO = 'remarcado'
    CANCELADO = 'cancelado'

class Agendamento(Base):
    """Modelo de agendamento de consultas com status e horários."""
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'), nullable=False)
    profissional_id = Column(Integer, ForeignKey('profissionais.id'), nullable=False)
    inicio = Column(DateTime, nullable=False)
    fim = Column(DateTime, nullable=False)
    status = Column(SQLAlchemyEnum(StatusAgendamento), default=StatusAgendamento.AGENDADO)  # Corrigido
    tipo_consulta = Column(String(50), default='presencial')

    paciente = relationship('Paciente')
    profissional = relationship('Profissional')

class LogAuditoria(Base):
    __tablename__ = 'logs_auditoria'
    id = Column(Integer, primary_key=True, index=True)
    acao = Column(String(100), nullable=False)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String(100))