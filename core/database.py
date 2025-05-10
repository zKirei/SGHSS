# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .models import Base  # Importe Base dos modelos

DATABASE_URL = "sqlite:///./sgss.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)  # Cria todas as tabelas

# Adicione esta função ↓
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()