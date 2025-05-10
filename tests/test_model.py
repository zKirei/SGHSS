# tests/test_model.py
import pytest
from datetime import datetime
from core.models import Paciente

def test_paciente_model(db):
    # Gerar dados únicos usando timestamp
    timestamp = datetime.now().strftime("%H%M%S%f")  # Adicione esta linha

    paciente = Paciente(
        cpf=f"123456789{timestamp[-6:]}",  # CPF único
        nome="Maria Silva",
        telefone=f"1199999{timestamp[-6:]}",  # Telefone único
        data_nascimento=datetime(2000, 1, 1).date()  # Campo obrigatório
    )

    db.add(paciente)
    db.commit()
    db.refresh(paciente)

    assert paciente.data_cadastro is not None
    assert paciente.data_cadastro <= datetime.now()