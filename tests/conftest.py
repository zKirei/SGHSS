# tests/conftest.py
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.models import Paciente, Profissional, LogAuditoria, Agendamento
from core.security import gerar_hash_senha

# Configuração do banco em memória para testes
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Permite concorrência segura
)

# Configuração do scoped_session para compatibilidade com testes
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Conexão com os eventos do SQLAlchemy para debug
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")  # Ativa FKs no SQLite
    cursor.close()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuração do banco de testes com dados iniciais"""
    # Recria o schema do zero para cada sessão de testes
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Popula dados de teste
    db = SessionLocal()
    try:
        # Pacientes de teste
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

        # Profissionais de teste
        profissionais = [
            Profissional(
                nome="Dr. Cardiologista",
                cpf="98765432100",
                especialidade="Cardiologia",
                hash_senha=gerar_hash_senha("SenhaSegura123!")
            ),
            Profissional(
                nome="Enf. Geral",
                cpf="00123456789",
                especialidade="Enfermeiro",
                hash_senha=gerar_hash_senha("OutraSenha456@")
            )
        ]

        # Agendamentos de teste
        agora = datetime.now()
        agendamentos = [
            Agendamento(
                paciente_id=1,
                profissional_id=1,
                inicio=agora + timedelta(hours=1),
                fim=agora + timedelta(hours=2),
                status="agendado"
            )
        ]

        # Adiciona todos os registros
        for obj in pacientes + profissionais + agendamentos:
            db.add(obj)
        
        db.commit()

        # Logs de auditoria
        db.add(LogAuditoria(
            acao="SETUP_INICIAL",
            usuario="SISTEMA",
            detalhes="População inicial de dados de teste"
        ))
        
        db.commit()

    except Exception as e:
        db.rollback()
        pytest.fail(f"Falha no setup do banco: {str(e)}")
    finally:
        db.close()

@pytest.fixture(scope="function")
def db():
    """Fornece uma nova sessão isolada para cada teste"""
    connection = engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)

    # Habilita o debug de consultas
    connection.execute = event.listens_for(connection, 'after_execute')(print)  # Opcional

    yield db

    # Limpeza pós-teste
    transaction.rollback()
    connection.close()

@pytest.fixture
def paciente_teste(db):
    return db.query(Paciente).filter_by(cpf="12345678909").first()

@pytest.fixture
def profissional_teste(db):
    return db.query(Profissional).filter_by(cpf="98765432100").first()

@pytest.fixture
def agendamento_teste(db):
    return db.query(Agendamento).filter_by(paciente_id=1).first()