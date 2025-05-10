from sqlalchemy.orm import Session
from sqlalchemy import extract
from .models import Agendamento, StatusAgendamento, Paciente
import csv
from datetime import datetime

def gerar_relatorio_pacientes(db: Session, arquivo_csv: str):
    pacientes = db.query(Paciente).all()
    with open(arquivo_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Nome', 'CPF', 'Data Nascimento', 'Telefone'])
        for paciente in pacientes:
            writer.writerow([
                paciente.id,
                paciente.nome,
                paciente.cpf,
                paciente.data_nascimento.isoformat() if paciente.data_nascimento else "",
                paciente.telefone
            ])
    return arquivo_csv

def gerar_relatorio_financeiro(db: Session, mes: int) -> float:
    total = db.query(Agendamento).filter(
        extract('month', Agendamento.inicio) == mes,
        Agendamento.status == StatusAgendamento.AGENDADO
    ).count()
    return total * 150.00  # Valor hipotético por consulta