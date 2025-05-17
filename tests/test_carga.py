from locust import HttpUser, task, between
from datetime import datetime, timedelta
import random
import logging
import uuid

logger = logging.getLogger("test_carga")

class CargaUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(0.5, 2.0)  # Reduza a carga com intervalos maiores

    def on_start(self):
        self.pacientes_ids = [1, 2, 3, 4, 5]
        self.profissionais_ids = [1, 2, 3]
        self.horarios_ocupados = {}  # profissional_id: lista de horários

    def gerar_horario_unico(self, profissional_id):
        for _ in range(10):  # Tentar até 10 vezes para evitar conflitos
            dias_no_futuro = random.randint(1, 365)
            hora_inicio = random.randint(8, 17)
            inicio = (
                datetime.now() + 
                timedelta(days=dias_no_futuro)
            ).replace(
                hour=hora_inicio,
                minute=0,
                second=0,
                microsecond=0
            ).isoformat()
            fim = (datetime.fromisoformat(inicio) + timedelta(hours=1)).isoformat()

            # Verificar conflitos em memória
            if profissional_id not in self.horarios_ocupados:
                self.horarios_ocupados[profissional_id] = []
            
            conflito = any(
                (inicio < existente["fim"] and fim > existente["inicio"])
                for existente in self.horarios_ocupados[profissional_id]
            )
            if not conflito:
                self.horarios_ocupados[profissional_id].append({"inicio": inicio, "fim": fim})
                return inicio, fim
        return None, None  # Falha após 10 tentativas

    @task
    def criar_agendamento(self):
        profissional_id = random.choice(self.profissionais_ids)
        paciente_id = random.choice(self.pacientes_ids)
        inicio, fim = self.gerar_horario_unico(profissional_id)

        if not inicio:
            logger.error("Não foi possível gerar horário único após 10 tentativas")
            return

        payload = {
            "paciente_id": paciente_id,
            "profissional_id": profissional_id,
            "inicio": inicio,
            "fim": fim,
            "request_id": str(uuid.uuid4())  # Identificador único para debug
        }

        try:
            with self.client.post(
                "/agendamentos",
                json=payload,
                catch_response=True,
                timeout=10  # Aumente o timeout
            ) as response:
                if response.status_code == 201:
                    logger.info(f"Sucesso! ID: {response.json()['id']}")
                else:
                    logger.error(f"Erro {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Falha na conexão: {str(e)}")