# tests/test_functional.py
import pytest
from datetime import datetime, timedelta  # Adicione datetime
from core.models import Paciente
from core.database import SessionLocal, init_db
from core.services import PacienteService, AgendamentoService
@pytest.fixture(scope="function")
def db():
    init_db()
    db = SessionLocal()
    yield db
    db.rollback()
    db.close()

def test_criar_paciente(db):
    # Corrigido: Definir timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    
    paciente = Paciente(
        cpf=f"123456789{timestamp[-5:]}",  # CPF único
        nome="Teste",
        telefone=f"1199999{timestamp[-5:]}",  # Telefone único
        data_nascimento=datetime(1990, 1, 1).date()  # Adicionado campo obrigatório
    )
    
    db.add(paciente)
    # Corrigido: Separar instruções
    db.commit()
    
    assert paciente.cpf is not None

def test_consentimento_lgpd_obrigatorio(db):
    """Garante que pacientes sem consentimento não sejam cadastrados"""
    with pytest.raises(ValueError):
        PacienteService.criar_paciente(db, {
            "cpf": "12345678909",
            "nome": "Teste",
            "telefone": "11999999999",
            "data_nascimento": "2000-01-01",
            "consentimento_lgpd": False  # Campo obrigatório
        })


def test_agendamento_passado(db):
    """Impede agendamentos em datas retroatas"""
    with pytest.raises(ValueError):
        AgendamentoService.agendar_consulta(db, {
            "paciente_id": 1,
            "profissional_id": 1,
            "inicio": datetime(2020, 1, 1, 10, 0),  # Objeto datetime
            "fim": datetime(2020, 1, 1, 11, 0)      # Objeto datetime
        })