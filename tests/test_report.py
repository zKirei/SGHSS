# tests/test_report.py
import pytest
from datetime import datetime
from core.database import SessionLocal
from core.reports import gerar_relatorio_financeiro
from core.models import Agendamento, StatusAgendamento

def test_relatorio_financeiro(db):
    # Crie um agendamento de teste
    agendamento = Agendamento(
        paciente_id=1,
        profissional_id=1,
        inicio=datetime(2024, 5, 10, 10, 0),
        fim=datetime(2024, 5, 10, 11, 0),
        status=StatusAgendamento.AGENDADO
    )
    db.add(agendamento)
    db.commit()

    mes_atual = 5  # Mês do agendamento criado
    resultado = gerar_relatorio_financeiro(db, mes_atual)
    assert resultado > 0  # Verifica se o relatório retorna um valor válido