# tests/test_functional.py
import pytest
from datetime import datetime, date
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
    paciente = Paciente(
        cpf="52998224725",  # CPF válido
        nome="Teste",
        telefone="(11) 99999-9999",
        data_nascimento=date(1990, 1, 1),
        consentimento_lgpd=True
    )
    
    db.add(paciente)
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

@pytest.mark.parametrize("data,esperado", [
    ("2000-02-30", ValueError),  # Data inválida
    ("3000-01-01", ValueError),  # Data futura
    ("1990-13-01", ValueError)   # Mês inválido
])
def test_datas_invalidas(db, data, esperado):
    with pytest.raises(esperado):
        PacienteService.criar_paciente(db, {
            "cpf": "12345678909",
            "nome": "Teste Data",
            "telefone": "11999999999",
            "data_nascimento": data,
            "consentimento_lgpd": True
        })