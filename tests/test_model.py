# tests/test_model.py
import pytest
from datetime import datetime
from core.models import Paciente

def test_paciente_model(db):
    timestamp = datetime.now().strftime("%H%M%S%f")
    cpf = f"123456789{timestamp[-6:]}"  # CPF único (apenas para teste)
    telefone = f"(11) 99999-{timestamp[-4:]}"  # Formato válido: (11) 99999-1234
    
    paciente = Paciente(
        cpf=cpf,
        nome="Maria Silva",
        telefone=telefone,  # Telefone válido
        data_nascimento=datetime(2000, 1, 1).date(),
        consentimento_lgpd=True
    )
    
    db.add(paciente)
    db.commit()
    assert paciente.data_cadastro <= datetime.now()