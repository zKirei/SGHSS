import pytest
from core.database import SessionLocal, init_db, Base, engine
from core.models import Paciente, Profissional
from datetime import date

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuração global do banco para todos os testes"""
    # Limpa e recria o banco apenas uma vez por sessão de testes
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Cria dados base (paciente e profissional)
    db = SessionLocal()
    try:
        # Paciente padrão - CORREÇÃO AQUI
        if not db.query(Paciente).filter_by(id=1).first():
            db.add(Paciente(
                id=1,
                nome="Paciente Teste",
                cpf="12345678909",
                data_nascimento=date(2000, 1, 1),  # Formato correto com inteiros
                telefone="11999999999",
                consentimento_lgpd=True
            ))
        
        # Profissional padrão
        if not db.query(Profissional).filter_by(id=1).first():
            db.add(Profissional(
                id=1,
                nome="Dr. Teste",
                cpf="98765432100",
                especialidade="Cardiologia",
                hash_senha="hash_temporario"
            ))
        
        db.commit()
    finally:
        db.close()

@pytest.fixture(scope="function")
def db():
    """Fornece uma sessão isolada para cada teste"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()