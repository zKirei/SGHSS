from locust import HttpUser, task, between, events
from datetime import datetime, timedelta
import random
import logging
import uuid
import time
from threading import Lock
from typing import Optional, List

logger = logging.getLogger("test_carga")

class CargaUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(1, 3)
    
    _horarios_ocupados = {}
    _db_lock = Lock()
    _cpfs_gerados = set()
    _telefones_gerados = set()

    def on_start(self):
        """Configuração inicial com verificações robustas"""
        self._aguardar_api_pronta()
        self.pacientes_ids = self._criar_entidades_com_retry("/pacientes", 5)
        self.profissionais_ids = self._criar_entidades_com_retry("/profissionais", 3)

    def _aguardar_api_pronta(self, max_tentativas=10):
        """Aguarda API ficar pronta com backoff exponencial"""
        for tentativa in range(max_tentativas):
            try:
                if self.client.get("/health", timeout=5).status_code == 200:
                    return
                time.sleep(2 ** tentativa)
            except Exception as e:
                logger.warning(f"Tentativa {tentativa+1}: API não respondendo - {str(e)}")
        raise ConnectionError("API não respondeu após {max_tentativas} tentativas")

    def _criar_entidades_com_retry(self, endpoint: str, quantidade: int, max_tentativas=3) -> List[int]:
        """Cria entidades com mecanismo de repetição"""
        ids = []
        for _ in range(quantidade):
            for tentativa in range(max_tentativas):
                payload = self._gerar_payload(endpoint)
                try:
                    with self._db_lock:  # Bloqueio para operações críticas
                        response = self.client.post(endpoint, json=payload, timeout=10)
                        
                        if response.status_code == 201 and response.json().get("id"):
                            ids.append(response.json()["id"])
                            break
                        
                        # Tratamento específico para erros de concorrência
                        if "database is locked" in response.text:
                            time.sleep(0.1 * (tentativa + 1))
                            continue
                        
                        self._reportar_falha(
                            endpoint=endpoint,
                            status=response.status_code,
                            mensagem=response.text
                        )
                except Exception as e:
                    self._reportar_falha(endpoint=endpoint, exception=e)
                    time.sleep(0.5)
            else:
                logger.error(f"Falha permanente ao criar {endpoint} após {max_tentativas} tentativas")
        return ids

    def _gerar_payload(self, endpoint: str) -> dict:
        """Gera payloads únicos e válidos"""
        with self._db_lock:  # Thread-safe para geração de dados
            payload = {
                "cpf": self._gerar_cpf_valido_unico(),
                "nome": f"Teste-{uuid.uuid4().hex[:6]}",
                "telefone": self._gerar_telefone_valido_unico(),
                "data_nascimento": "2000-01-01",
                "consentimento_lgpd": True
            }
            
            if endpoint == "/profissionais":
                payload.update({
                    "especialidade": random.choice(["médico", "enfermeiro", "outro"]),
                    "senha": f"Senha@{uuid.uuid4().hex[:8]}"
                })
            return payload

    def _gerar_cpf_valido_unico(self) -> str:
        """Gera CPFs válidos únicos com verificação de dígitos"""
        while True:
            # Geração correta de CPF válido
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

    def _gerar_telefone_valido_unico(self) -> str:
        """Gera números de telefone no formato brasileiro"""
        while True:
            ddd = random.choice(["11", "21", "31", "48", "51"])
            numero = f"9{random.randint(1000000, 9999999)}"  # Números móveis
            completo = f"({ddd}) {numero[:4]}-{numero[4:]}"
            if completo not in self._telefones_gerados:
                self._telefones_gerados.add(completo)
                return completo

    def _reportar_falha(self, endpoint: str, status: Optional[int] = None, 
                      mensagem: Optional[str] = None, exception: Optional[Exception] = None):
        """Log detalhado de falhas"""
        erro = f"Falha em {endpoint}: "
        if status:
            erro += f"[Status {status}] "
        if mensagem:
            erro += f"Resposta: {mensagem[:200]} "
        if exception:
            erro += f"Exceção: {str(exception)}"
            
        logger.error(erro)
        events.request.fire(
            request_type="POST",
            name=f"{endpoint}/Error",
            response_time=0,
            response_length=0,
            exception=exception,
            context={"endpoint": endpoint, "payload": mensagem},
            url=endpoint
        )

    @task(3)
    def criar_agendamento(self):
        """Tarefa principal com tratamento robusto de erros"""
        if not self.profissionais_ids or not self.pacientes_ids:
            self._reportar_falha("Agendamento", mensagem="Entidades não inicializadas")
            return

        try:
            profissional_id = random.choice(self.profissionais_ids)
            paciente_id = random.choice(self.pacientes_ids)
            inicio, fim = self._gerar_horario_unico(profissional_id)

            if not inicio:
                self._reportar_falha("Agendamento", mensagem="Conflito de horário")
                return

            payload = {
                "paciente_id": paciente_id,
                "profissional_id": profissional_id,
                "inicio": inicio,
                "fim": fim,
                "tipo_consulta": random.choice(["presencial", "telemedicina"])
            }

            with self.client.post("/agendamentos", json=payload, catch_response=True) as response:
                if response.status_code == 201 and response.json().get("id"):
                    response.success()
                else:
                    self._reportar_falha("/agendamentos", status=response.status_code, mensagem=response.text)

        except Exception as e:
            self._reportar_falha("/agendamentos", exception=e)

    def _gerar_horario_unico(self, profissional_id: int) -> tuple:
        """Gera horários sem conflitos com algoritmo otimizado"""
        with self._db_lock:
            registros = self._horarios_ocupados.setdefault(profissional_id, [])
            
            for _ in range(5):  # Tenta 5 horários diferentes
                dia = datetime.now() + timedelta(days=random.randint(1, 30))
                inicio = dia.replace(
                    hour=random.randint(8, 18),
                    minute=0,
                    second=0,
                    microsecond=0
                )
                fim = inicio + timedelta(hours=1)

                # Verificação de sobreposição eficiente
                if not any(
                    (inicio <= existente["fim"]) and (fim >= existente["inicio"])
                    for existente in registros
                ):
                    registros.append({"inicio": inicio, "fim": fim})
                    return inicio.isoformat(), fim.isoformat()
            
            return None, None

    @task(1)
    def consultar_paciente(self):
        """Tarefa secundária para simular consultas"""
        if self.pacientes_ids:
            paciente_id = random.choice(self.pacientes_ids)
            with self.client.get(f"/pacientes/{paciente_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    self._reportar_falha("/pacientes/{id}", status=response.status_code)