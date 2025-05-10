# tests/conftest.py
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from core.database import Base
from core.models import Paciente, Profissional, LogAuditoria
from core.security import gerar_hash_senha

# Configuração do banco em memória para testes
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Permite acesso concorrente seguro
)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuração do banco de testes uma vez por sessão"""
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Popula dados iniciais
    db = SessionLocal()
    try:
        # Dados básicos para os testes
        pacientes = [
            Paciente(
                nome="Paciente Teste 1",
                cpf="12345678909",
                data_nascimento=date(2000, 1, 1),
                telefone="11999999999",
                consentimento_lgpd=True
            ),
            Paciente(
                nome="Paciente Teste 2",
                cpf="00987654321",
                data_nascimento=date(2010, 5, 15),
                telefone="21999999999",
                consentimento_lgpd=True
            )
        ]
        
        profissionais = [
            Profissional(
                nome="Dr. Cardiologista",
                cpf="98765432100",
                especialidade="Cardiologia",
                hash_senha=gerar_hash_senha("Cardio@2023")
            ),
            Profissional(
                nome="Enf. Geral",
                cpf="00123456789",
                especialidade="Enfermeiro",
                hash_senha=gerar_hash_senha("Enfermagem123")
            )
        ]
        
        db.add_all(pacientes + profissionais)
        db.commit()
        
        # Logs demonstrativos
        logs = [
            LogAuditoria(
                acao="CADASTRO_INICIAL",
                usuario="SISTEMA"
            )
        ]
        db.add_all(logs)
        db.commit()
        
    finally:
        db.close()

@pytest.fixture(scope="function")
def db():
    """Fornece uma transação isolada para cada teste"""
    connection = engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)
    
    yield db  # Teste roda aqui
    
    # Rollback após o teste
    transaction.rollback()
    connection.close()

@pytest.fixture
def paciente_teste(db):
    """Fixture para obter o paciente de teste"""
    return db.query(Paciente).filter_by(cpf="12345678909").first()

@pytest.fixture
def profissional_teste(db):
    """Fixture para obter o profissional de teste"""
    return db.query(Profissional).filter_by(cpf="98765432100").first()