# tests/conftest.py (versão corrigida)
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.database import Base
from core.models import Paciente, Profissional, Agendamento
from core.security import gerar_hash_senha

# Configuração do banco em memória
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Configuração CORRETA da sessão
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuração inicial do banco de testes"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)  # Cria todas as tabelas

    # Popula dados de teste
    db = SessionLocal()
    try:
        # Pacientes (use CPFs válidos)
        pacientes = [
            Paciente(
                nome="Paciente Teste 1",
                cpf="52998224725",  # ← CPF válido
                data_nascimento=date(2000, 1, 1),
                telefone="(11) 99999-9999",
                consentimento_lgpd=True
            )
        ]

        # Profissionais
        profissionais = [
            Profissional(
                nome="Dr. Teste",
                cpf="98765432109",  # ← CPF válido
                especialidade="Cardiologia",
                hash_senha=gerar_hash_senha("Senha123@")
            )
        ]

        # Agendamentos
        agendamentos = [
            Agendamento(
                paciente_id=1,
                profissional_id=1,
                inicio=datetime.now() + timedelta(hours=1),
                fim=datetime.now() + timedelta(hours=2),
                status="agendado"
            )
        ]

        # Adiciona todos os registros
        for obj in pacientes + profissionais + agendamentos:
            db.add(obj)
        
        db.commit()

    except Exception as e:
        db.rollback()
        pytest.fail(f"Falha no setup: {str(e)}")
    finally:
        db.close()

@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# Fixtures para entidades de teste
@pytest.fixture
def paciente_teste(db):
    return db.query(Paciente).filter_by(cpf="52998224725").first()

@pytest.fixture
def agendamento_teste(db):
    return db.query(Agendamento).first()