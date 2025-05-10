import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.security import sanitizar_input
from core.services import PacienteService
from core.database import SessionLocal
from concurrent.futures import ThreadPoolExecutor

class TestSecurity:
    """Classe de testes para funcionalidades de segurança"""

    # ------------------------------------------
    # Testes de Sanitização
    # ------------------------------------------
    @pytest.mark.parametrize("input,esperado", [
        ("<script>alert(1)</script>", "script alert 1 script"),
        ("'; DROP TABLE pacientes;--", " DROP TABLE pacientes "),  # Espaços adicionais por segurança
        ("João Silva' OR '1'='1", "João Silva OR 1 1"),
        ("Normal\nInput\tTest", "Normal Input Test")
    ])
    def test_sanitizacao_casos(self, input, esperado):
        assert sanitizar_input(input) == esperado

    # ------------------------------------------
    # Testes de Concorrência com CPFs Válidos
    # ------------------------------------------
    def test_concorrencia_cpf(self):
        """Verifica inserções concorrentes de CPFs válidos e únicos"""

        def gerar_cpf_valido(base: int) -> str:
            """Gera CPFs válidos para testes."""
            cpf_base = f"{base:09d}"  # 9 dígitos
            # Cálculo do primeiro dígito verificador
            soma = sum(int(cpf_base[i]) * (10 - i) for i in range(9))
            d1 = (soma * 10) % 11
            d1 = d1 if d1 < 10 else 0
            # Cálculo do segundo dígito verificador
            soma = sum(int(cpf_base[i]) * (11 - i) for i in range(9)) + d1 * 2
            d2 = (soma * 10) % 11
            d2 = d2 if d2 < 10 else 0
            return f"{cpf_base}{d1}{d2}"

        def criar_paciente(cpf: str):
            """Tenta criar um paciente com CPF único"""
            engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)
            db = Session()
            try:
                PacienteService.criar_paciente(db, {
                    "cpf": cpf,
                    "nome": "Concorrente",
                    "telefone": "(11) 99999-9999",  # Telefone válido
                    "data_nascimento": "2000-01-01",
                    "consentimento_lgpd": True
                })
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                return False
            finally:
                db.close()

        # Gera 20 CPFs válidos únicos usando timestamp
        timestamp = int(time.time() * 1000) % 10**9  # 9 dígitos
        cpfs = [gerar_cpf_valido(timestamp + i) for i in range(20)]

        # Executa em paralelo
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(criar_paciente, cpfs))

        # Verificação
        assert sum(results) == 20, "Todos os CPFs válidos devem ser inseridos"