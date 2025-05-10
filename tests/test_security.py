class TestSecurity:
    @pytest.mark.parametrize("input,esperado", [
        ("<script>alert(1)</script>", "script alert 1 script"),
        ("'; DROP TABLE pacientes;--", "DROP TABLE pacientes"),
        ("João Silva' OR '1'='1", "João Silva OR 1 1"),
        ("Normal\nInput\tTest", "Normal Input Test")
    ])
    def test_sanitizacao_casos(self, input, esperado):
        assert sanitizar_input(input) == esperado

    def test_concorrencia_cpf(self, db):
        from concurrent.futures import ThreadPoolExecutor
        
        def criar_paciente(cpf):
            try:
                PacienteService.criar_paciente(db, {
                    "cpf": cpf,
                    "nome": "Concorrente",
                    "telefone": "11999999999",
                    "data_nascimento": "2000-01-01",
                    "consentimento_lgpd": True
                })
                return True
            except:
                return False
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            cpf_base = "123456789"
            results = list(executor.map(
                criar_paciente, 
                [f"{cpf_base}{i:02d}" for i in range(20)]
            ))
        
        successes = sum(results)
        assert successes == 1, "Deveria haver apenas 1 sucesso por unique constraint"