from locust import HttpUser, task, between
from core.models import Agendamento
from core.database import SessionLocal
import logging

logger = logging.getLogger("test_carga")

class CargaUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(0.1, 0.5)

    @task
    def criar_agendamento(self):
        payload = {
            "paciente_id": 1,
            "profissional_id": 1,
            "inicio": "2025-05-10T09:00:00",
            "fim": "2025-05-10T10:00:00"
        }

        with self.client.post("/agendamentos", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                logger.info("Agendamento criado com sucesso")
            else:
                logger.error(f"Falha: {response.status_code} - {response.text}")

def test_verificar_agendamentos():
    db = SessionLocal()
    try:
        total = db.query(Agendamento).count()
        print(f"Agendamentos registrados: {total}")
    finally:
        db.close()