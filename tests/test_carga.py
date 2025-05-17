from locust import HttpUser, task, between, tag
from datetime import datetime, timedelta
import random
import logging
import uuid
import time
from threading import Lock

logger = logging.getLogger("test_carga")

class CargaUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(1, 3)  # Intervalo mais realista

    # Variáveis de classe para controle de estado compartilhado
    _horarios_ocupados = {}
    _lock = Lock()

    def on_start(self):
        # Verifica se a API está online
        for _ in range(10):
            try:
                if self.client.get("/health").status_code == 200:
                    break
            except Exception as e:
                logger.error(f"Falha ao conectar: {str(e)}")
                time.sleep(2)
        else:
            raise Exception("API offline após 10 tentativas")

        # Criar pacientes e profissionais dinamicamente
        self.pacientes_ids = self._criar_entidades("/pacientes", 5)
        self.profissionais_ids = self._criar_entidades("/profissionais", 3)

    def _criar_entidades(self, endpoint, quantidade):
        ids = []
        for _ in range(quantidade):
            payload = {
                "cpf": self.gerar_cpf_valido(),
                "nome": f"Teste {uuid.uuid4().hex[:6]}",
                "telefone": "(11) 99999-9999",
                "data_nascimento": "2000-01-01",
                "consentimento_lgpd": True
            }
        
            # Ajuste para o endpoint de profissionais
            if endpoint == "/profissionais":
                payload.update({
                    "especialidade": "médico",  # Valor válido conforme o Enum
                    "senha": "SenhaSegura123@"  # Campo obrigatório
                })

            response = self.client.post(endpoint, json=payload)
            if response.status_code == 201:
                ids.append(response.json().get("id"))
            else:
                logger.error(f"Erro criando {endpoint}: {response.text}")
        return ids

    def gerar_cpf_valido(self):
        cpf = [random.randint(0,9) for _ in range(9)]
        
        # Calcula primeiro dígito
        soma = sum(x * (10 - i) for i, x in enumerate(cpf))
        d1 = 11 - (soma % 11)
        cpf.append(d1 if d1 < 10 else 0)
        
        # Calcula segundo dígito
        soma = sum(x * (11 - i) for i, x in enumerate(cpf))
        d2 = 11 - (soma % 11)
        cpf.append(d2 if d2 < 10 else 0)
        
        return ''.join(map(str, cpf))

    def gerar_horario_unico(self, profissional_id):
        with self._lock:
            if profissional_id not in self._horarios_ocupados:
                self._horarios_ocupados[profissional_id] = []

            for _ in range(5):  # Tenta 5 vezes
                dia = datetime.now() + timedelta(days=random.randint(1, 30))
                inicio = dia.replace(
                    hour=random.randint(8, 18),
                    minute=0,
                    second=0,
                    microsecond=0
                )
                fim = inicio + timedelta(hours=1)

                # Verifica conflitos
                conflito = any(
                    (inicio < existente["fim"] and fim > existente["inicio"])
                    for existente in self._horarios_ocupados[profissional_id]
                )

                if not conflito:
                    self._horarios_ocupados[profissional_id].append({
                        "inicio": inicio.isoformat(),
                        "fim": fim.isoformat()
                    })
                    return inicio.isoformat(), fim.isoformat()
            return None, None
        
    @tag("carga")
    @task
    def criar_agendamento(self):
        if not self.profissionais_ids or not self.pacientes_ids:
            logger.error("Entidades não foram criadas corretamente")
            self.environment.events.request.fire(
                request_type="POST",
                name="Agendamento/SetupError",
                response_time=0,
                exception=Exception("Falha no setup"),
            )
            return

        profissional_id = random.choice(self.profissionais_ids)
        paciente_id = random.choice(self.pacientes_ids)
        inicio, fim = self.gerar_horario_unico(profissional_id)

        if not inicio:
            logger.error(f"Falha ao gerar horário para profissional {profissional_id}")
            return

        payload = {
            "paciente_id": paciente_id,
            "profissional_id": profissional_id,
            "inicio": inicio,
            "fim": fim,
            "request_id": str(uuid.uuid4())
        }

        try:
            with self.client.post(
                "/agendamentos",
                json=payload,
                catch_response=True,
                timeout=10
            ) as response:
                if response.ok:
                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")
        except Exception as e:
            response.failure(f"Execção: {str(e)}")