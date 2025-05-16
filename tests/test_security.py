# tests/test_security.py (versão corrigida)
import pytest
import random
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ThreadPoolExecutor
from core.models import Paciente
from core.database import Base, SessionLocal
from sqlalchemy.exc import IntegrityError

# Configuração ÚNICA do banco (compartilhado entre threads)
TEST_DB_URL = "sqlite:///test_concorrencia.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)  # Renomeado para evitar conflito

@pytest.mark.parametrize("input,esperado", [
    ("<script>alert(1)</script>", "alert 1"),
    ("'; DROP TABLE pacientes;--", "TABLE pacientes"),
    ("João Silva' OR '1'='1", "João Silva 1 1"),
])
def test_sanitizacao(input, esperado):
    from core.security import sanitizar_input
    assert sanitizar_input(input) == esperado

def test_concorrencia_cpf():
    """Testa inserções concorrentes com CPFs únicos e válidos"""
    
    def gerar_cpf_unico() -> str:
        cpf = [random.randint(0, 9) for _ in range(9)]
    
        # Calcula primeiro dígito
        soma = sum(x * (10 - i) for i, x in enumerate(cpf))
        d1 = 11 - (soma % 11)
        cpf.append(d1 if d1 < 10 else 0)
    
        # Calcula segundo dígito
        soma = sum(x * (11 - i) for i, x in enumerate(cpf))
        d2 = 11 - (soma % 11)
        cpf.append(d2 if d2 < 10 else 0)
    
        return ''.join(map(str, cpf))
    
    cpfs = [gerar_cpf_unico() for _ in range(50)]

    def inserir_paciente(cpf: str):
        """Tenta inserir um paciente com controle transacional"""
        db = SessionLocal()
        try:
            # Verifica se o CPF já existe
            if db.query(Paciente).filter_by(cpf=cpf).first():
                return False
            
            novo_paciente = Paciente(
                cpf=cpf,
                nome="Concorrente Teste",
                telefone="11999999999",
                data_nascimento=date(2000, 1, 1),
                consentimento_lgpd=True
            )
            db.add(novo_paciente)
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False
        finally:
            db.close()

    # Executa com 10 workers
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(inserir_paciente, cpfs))

    sucessos = sum(results)
    assert sucessos == 50, f"Sucessos: {sucessos}/50"


def test_sql_injection_paciente(db):
    """Testa resistência a injeção de SQL no cadastro"""
    from core.services import PacienteService
    with pytest.raises(ValueError) as exc_info:
        PacienteService.criar_paciente(db, {
            "cpf": "12345678909'; DROP TABLE pacientes;--",
            "nome": "Teste'; DELETE FROM pacientes;--",
            "telefone": "11999999999", 
            "data_nascimento": "2000-01-01",
            "consentimento_lgpd": True
        })
    assert "inválido" in str(exc_info.value).lower()