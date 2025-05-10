import pytest
from core.security import sanitizar_input, gerar_hash_senha, verificar_senha
from core.services import PacienteService
from core.database import SessionLocal

class TestSecurity:
    """Classe de testes para funcionalidades de segurança"""
    
    def test_hash_senha(self):
        """Testa geração e verificação de hash de senha"""
        senha = "senhaSegura123"
        hash = gerar_hash_senha(senha)
        
        # Verifica senha correta
        assert verificar_senha(senha, hash) is True
        
        # Verifica senha incorreta
        assert not verificar_senha("senhaErrada", hash)
        
        # Verifica que hashes são diferentes para mesma senha
        hash2 = gerar_hash_senha(senha)
        assert hash != hash2
    
    def test_sql_injection_prevencao(self):
        """Testa prevenção contra injeção SQL no cadastro de pacientes"""
        db = SessionLocal()
        try:
            paciente = PacienteService.criar_paciente(
                db,
                {
                    "nome": "Admin'; DROP TABLE usuarios;--",
                    "cpf": "12345678909",
                    "telefone": "11999999999",
                    "data_nascimento": "2000-01-01",
                    "consentimento_lgpd": True
                }
            )
            # Verifica que caracteres/sequências perigosas foram removidas
            assert "DROP TABLE" not in paciente.nome
            assert ";" not in paciente.nome
            assert "--" not in paciente.nome
            assert "'" not in paciente.nome
        finally:
            db.close()
    
    def test_xss_prevencao(self):
        """Testa prevenção contra XSS no cadastro de pacientes"""
        db = SessionLocal()
        try:
            paciente = PacienteService.criar_paciente(
                db,
                {
                    "nome": "<script>alert('XSS')</script>",
                    "cpf": "98765432100",
                    "telefone": "21999999999",
                    "data_nascimento": "1990-01-01",
                    "consentimento_lgpd": True
                }
            )
            # Verifica que tags foram removidas mas conteúdo interno pode permanecer
            assert "<script>" not in paciente.nome
            assert "</script>" not in paciente.nome
        finally:
            db.close()
    
    def test_sanitizacao_unicode(self):
        """Testa sanitização com caracteres Unicode"""
        assert sanitizar_input("Café; DROP TABLE") == "Café DROP TABLE"
        assert sanitizar_input("Mötörhëäd--") == "Mötörhëäd"
    
    def test_sanitizacao_espacos(self):
        """Testa normalização de espaços em branco"""
        assert sanitizar_input("  Teste   com  espaços  ") == "Teste com espaços"
        assert sanitizar_input("Teste\t\n\rcom\tcaracteres") == "Teste com caracteres"