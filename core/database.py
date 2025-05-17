# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .models import Base

# Configuração do banco de dados em memória para testes
DATABASE_URL = "sqlite:///test.db"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,  # Forçar uso do QueuePool
    pool_size=100,
    pool_pre_ping=True,  #ajuste conforme necessidade
    max_overflow=200, #ajuste conforme necessidade
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    """Função para inicializar o banco de dados"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Fornece uma instância de banco de dados para cada requisição
    Fechamento automático após o uso
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()