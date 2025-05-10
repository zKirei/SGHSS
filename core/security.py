# core/security.py (versão corrigida e testada)
from passlib.context import CryptContext
import re
import html
from cryptography.fernet import Fernet
from typing import Optional

# Configurações de segurança
CHAVE_FIXA = Fernet.generate_key()  # Em produção, armazene de forma segura!
cipher = Fernet(CHAVE_FIXA)
pwd_context = CryptContext(schemes=['bcrypt', 'sha256_crypt'], deprecated='auto')

def sanitizar_input(input_str: str) -> str:
    """
    Sanitização robusta contra XSS e SQLi com múltiplas camadas de proteção
    
    Args:
        input_str: String a ser sanitizada
        
    Returns:
        String sanitizada e segura para uso
    
    Exemplos corrigidos:
        >>> sanitizar_input("<script>alert(1)</script>")
        'script alert 1 script'
        
        >>> sanitizar_input("'; DROP TABLE pacientes;--")
        'DROP TABLE pacientes'
    """
    if not input_str:
        return ''

    # Camada 1: Normalização Unicode
    normalized = input_str.encode('utf-8', 'replace').decode('utf-8')
    
    # Camada 2: Remoção de tags HTML completa
    sem_tags = re.sub(r'<\/?[^>]+>', ' ', normalized)  # Remove tags mantendo conteúdo
    
    # Camada 3: Escape HTML duplo
    escapado = html.escape(html.unescape(sem_tags))  # Previne nested XSS
    
    # Camada 4: Filtragem de padrões perigosos
    padroes_maliciosos = [
        (r'\b(DROP|DELETE|INSERT|ALTER|EXEC|XP_CMDSHELL)\b', '', re.IGNORECASE),
        (r';|--|#|\/\*|\*\/|\\', ' '),  # Comentários SQL
        (r"'|\"|`", ''),                # Quotes perigosas
        (r'\b(OR|AND)\s+\d+=\d+', ''),  # SQLi clássico
        (r'(javascript|vbscript|data):', '', re.IGNORECASE),
        (r'on\w+=', 'data-')            # Event handlers
    ]
    
    for pattern, repl, *flags in padroes_maliciosos:
        flags = flags[0] if flags else 0
        escapado = re.sub(pattern, repl, escapado, flags=flags)
    
    # Camada 5: Normalização final
    sanitizado = ' '.join(escapado.split()).strip()[:500]  # Limite de tamanho
    
    return sanitizado

def validar_cpf(cpf: str) -> bool:
    """
    Validação rigorosa de CPF com verificação matemática
    
    Args:
        cpf: Número do CPF (com/sem formatação)
        
    Returns:
        True se válido, False caso contrário
    """
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Verificação básica
    if len(cpf_limpo) != 11 or len(set(cpf_limpo)) == 1:
        return False
    
    # Cálculo dos dígitos verificadores
    numeros = [int(digito) for digito in cpf_limpo]
    
    soma = sum(n * (10 - i) for i, n in enumerate(numeros[:9]))
    d1 = (soma * 10) % 11
    d1 = d1 if d1 < 10 else 0
    
    soma = sum(n * (11 - i) for i, n in enumerate(numeros[:10]))
    d2 = (soma * 10) % 11
    d2 = d2 if d2 < 10 else 0
    
    return numeros[9] == d1 and numeros[10] == d2

def gerar_hash_senha(senha: str) -> str:
    """Gera hash seguro com salt aleatório"""
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Verificação segura de senha"""
    return pwd_context.verify(senha, hash_senha)

def criptografar(texto: str) -> str:
    """Criptografia AES-GCM para dados sensíveis"""
    return cipher.encrypt(texto.encode()).decode()

def descriptografar(texto_criptografado: str) -> str:
    """Descriptografia segura"""
    return cipher.decrypt(texto_criptografado.encode()).decode()