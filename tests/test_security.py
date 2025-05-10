import pytest
from core.security import sanitizar_input, gerar_hash_senha, verificar_senha
from core.services import PacienteService
from core.database import SessionLocal
from concurrent.futures import ThreadPoolExecutor

class TestSecurity:
    """Classe de testes para funcionalidades de segurança"""
    
    @pytest.mark.parametrize("input,esperado", [
        ("<script>alert(1)</script>", "script alert 1 script"),
        ("'; DROP TABLE pacientes;--", "DROP TABLE pacientes"), 
        ("João Silva' OR '1'='1", "João Silva OR 1 1"),
        ("Normal\nInput\tTest", "Normal Input Test")
    ])
    def test_sanitizacao_casos(self, input, esperado):
        assert sanitizar_input(input) == esperado

    def test_concorrencia_cpf(self):

        def criar_paciente(cpf):
            db = SessionLocal()
            try:
                PacienteService.criar_paciente(db, {
                    "cpf": cpf,
                    "nome": "Concorrente",
                    "telefone": "(11) 99999-9999",
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
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            cpf_base = "5299822472"
            results = list(executor.map(
                criar_paciente, 
                [f"{cpf_base[:-2]}{i:02d}" for i in range(20)]
            ))
        
        assert sum(results) == 1, "Apenas 1 deve ser unico"
