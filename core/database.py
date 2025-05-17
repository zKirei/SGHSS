# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .models import Base  # Importação correta da Base

# Configuração do banco de dados em memória para testes
DATABASE_URL = "sqlite:///test.db?check_same_thread=False"  # Arquivo físico
engine = create_engine(
    DATABASE_URL,
    pool_size=100,
    max_overflow=50,
    pool_pre_ping=True  # Verifica conexões antes de usar
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