from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base, validates, Session
from sqlalchemy import Enum as SQLAlchemyEnum
from datetime import datetime, date
from enum import Enum
import re

Base = declarative_base()

class Paciente(Base):
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
    # Aceita (11) 99999-9999, 11999999999, 1199999999 (8 ou 9 dígitos)
    if not re.match(r'^(\(\d{2}\)\s?)?(9?\d{4}-?\d{4})$', value):
        raise ValueError("Telefone inválido. Exemplos: (11) 99999-9999 ou 11999999999")
    return value

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
    __tablename__ = 'logs_auditoria'
    
    id = Column(Integer, primary_key=True)
    acao = Column(String(50), nullable=False)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String(50), nullable=False)
    detalhes = Column(String(500))

    # Método de registro simplificado
    @classmethod
    def registrar(cls, db: Session, acao: str, usuario: str, detalhes: str):
        log = cls(acao=acao, usuario=usuario, detalhes=detalhes)
        db.add(log)