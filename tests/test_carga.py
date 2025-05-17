from locust import HttpUser, task, between, events
from datetime import datetime, timedelta
import random
import logging
import uuid
import time
from threading import Lock
from typing import Optional

logger = logging.getLogger("test_carga")

class CargaUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(2, 5)
    
    _horarios_ocupados = {}
    _db_lock = Lock()
    _cpfs_gerados = set()
    _telefones_gerados = set()

    def on_start(self):
        self._aguardar_api_pronta()
        self.pacientes_ids = self._criar_entidades("/pacientes", 5)
        self.profissionais_ids = self._criar_entidades("/profissionais", 3)

    def _aguardar_api_pronta(self):
        for _ in range(10):
            try:
                if self.client.get("/health", timeout=5).status_code == 200:
                    return
            except Exception as e:
                logger.debug(f"API não respondendo: {str(e)}")
                time.sleep(2)
        raise ConnectionError("API não respondeu após 10 tentativas")

    def _criar_entidades(self, endpoint: str, quantidade: int) -> list:
        ids = []
        for _ in range(quantidade):
            payload = self._gerar_payload(endpoint)
            try:
                with self.client.post(endpoint, json=payload, catch_response=True) as response:
                    if response.status_code == 201:
                        ids.append(response.json().get("id"))
                    else:
                        self._reportar_falha(
                            endpoint=endpoint,
                            status=response.status_code,
                            mensagem=response.text
                        )
            except Exception as e:
                self._reportar_falha(endpoint=endpoint, exception=e)
        return ids

    def _gerar_payload(self, endpoint: str) -> dict:
        payload = {
            "cpf": self._gerar_cpf_unico(),
            "nome": f"Teste-{uuid.uuid4().hex[:6]}",
            "telefone": self._gerar_telefone_unico(),
            "data_nascimento": "2000-01-01",
            "consentimento_lgpd": True
        }
        
        if endpoint == "/profissionais":
            payload.update({
                "especialidade": "médico",
                "senha": "SenhaSegura123@"
            })
        return payload

    def _gerar_cpf_unico(self) -> str:
        while True:
            cpf = [random.randint(0,9) for _ in range(9)]
            
            # Cálculo do primeiro dígito
            soma = sum(x * (10 - i) for i, x in enumerate(cpf))
            d1 = 11 - (soma % 11)
            cpf.append(d1 if d1 < 10 else 0)
            
            # Cálculo do segundo dígito
            soma = sum(x * (11 - i) for i, x in enumerate(cpf))
            d2 = 11 - (soma % 11)
            cpf.append(d2 if d2 < 10 else 0)
            
            cpf_str = ''.join(map(str, cpf))
            if cpf_str not in self._cpfs_gerados:
                self._cpfs_gerados.add(cpf_str)
                return cpf_str

    def _gerar_telefone_unico(self) -> str:
        while True:
            numero = f"11{random.randint(80000000, 99999999)}"
            if numero not in self._telefones_gerados:
                self._telefones_gerados.add(numero)
                return f"({numero[:2]}) {numero[2:7]}-{numero[7:]}"

    def _reportar_falha(self, endpoint: str, status: Optional[int] = None, 
                      mensagem: Optional[str] = None, exception: Optional[Exception] = None):
        erro = f"Falha criando {endpoint}: "
        if status:
            erro += f"Status {status} - "
        if mensagem:
            erro += f"Resposta: {mensagem[:200]}"
        if exception:
            erro += f"Exceção: {str(exception)}"
            
        logger.error(erro)
        events.request.fire(
            request_type="POST",
            name=f"{endpoint}/Error",
            response_time=0,
            response_length=0,
            exception=exception,
            context={},
            url=endpoint
        )

    def gerar_horario_unico(self, profissional_id: int) -> tuple:
        with self._lock:
            registros = self._horarios_ocupados.setdefault(profissional_id, [])
            
            for _ in range(5):
                inicio = datetime.now().replace(
                    hour=random.randint(8, 18),
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(days=random.randint(1, 30))
                
                fim = inicio + timedelta(hours=1)
                
                if not any(
                    inicio < existente["fim"] and fim > existente["inicio"]
                    for existente in registros
                ):
                    registros.append({"inicio": inicio, "fim": fim})
                    return inicio.isoformat(), fim.isoformat()
            return None, None

    @task
    def criar_agendamento(self):
        if not self.profissionais_ids or not self.pacientes_ids:
            self._reportar_falha(
                endpoint="Agendamento",
                mensagem="Falha no setup: Entidades não criadas"
            )
            return

        profissional_id = random.choice(self.profissionais_ids)
        paciente_id = random.choice(self.pacientes_ids)
        inicio, fim = self.gerar_horario_unico(profissional_id)

        if not inicio:
            self._reportar_falha(
                endpoint="Agendamento",
                mensagem="Falha ao gerar horário único"
            )
            return

        payload = {
            "paciente_id": paciente_id,
            "profissional_id": profissional_id,
            "inicio": inicio,
            "fim": fim,
            "tipo_consulta": "presencial"
        }

        try:
            with self.client.post(
                "/agendamentos",
                json=payload,
                catch_response=True,
                timeout=10
            ) as response:
                if response.status_code == 201:
                    response.success()
                else:
                    self._reportar_falha(
                        endpoint="/agendamentos",
                        status=response.status_code,
                        mensagem=response.text
                    )
        except Exception as e:
            self._reportar_falha(
                endpoint="/agendamentos",
                exception=e
            )