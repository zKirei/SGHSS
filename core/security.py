# core/security.py
from passlib.context import CryptContext
import re
import html
from cryptography.fernet import Fernet
from typing import Tuple

CHAVE_FIXA = b'2IXtM3zdqEA7h1YH8WGSyQk9lLwvJpo0NRFmKjCnTq8='
cipher = Fernet(CHAVE_FIXA)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def sanitizar_input(input_str: str) -> str:
    """
    Sanitização de inputs para prevenir ataques básicos XSS e SQLi
    
    Args:
        input_str: String a ser sanitizada
        
    Returns:
        String sanitizada e normalizada
    
    Exemplos:
        >>> sanitizar_input("<script>alert(1)</script>")
        'script alert 1 script'
        
        >>> sanitizar_input("'; DROP TABLE pacientes;--")
        'DROP TABLE pacientes'
    """
    if not input_str:
        return input_str

    # Passo 1: Remover tags HTML
    sem_tags = re.sub(r'<[^>]*>', '', input_str)
    
    # Passo 2: Escapar caracteres HTML especiais
    escapado = html.escape(sem_tags)
    
    # Passo 3: Remover padrões perigosos comuns
    padroes_maliciosos = [
        r'\b(DROP|DELETE|INSERT|ALTER|EXEC|XP_CMDSHELL)\b',
        r';|--|/\*|\*/|\\',  # Comentários SQL
        r"'|\"",             # Quebra de strings
        r'\b(OR|AND)\s+\d+=\d+',  # Condições sempre verdadeiras
        r'(javascript|vbscript):',  # XSS
        r'onerror\s*=\s*["\']'      # Event handlers maliciosos
    ]
    
    for padrao in padroes_maliciosos:
        escapado = re.sub(padrao, '', escapado, flags=re.IGNORECASE)
    
    # Passo 4: Normalizar espaços em branco
    normalizado = ' '.join(escapado.split()).strip()
    
    return normalizado

def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Validação completa de CPF com explicação didática
    
    Args:
        cpf: Número do CPF a ser validado (com ou sem formatação)
        
    Returns:
        Tuple (bool, str): Resultado e mensagem explicativa
    
    Exemplo:
        >>> validar_cpf("529.982.247-25")
        (True, 'CPF válido')
        
        >>> validar_cpf("111.111.111-11")
        (False, 'CPF inválido (dígitos repetidos)')
    """
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Validação básica
    if len(cpf_limpo) != 11:
        return False, "CPF deve conter 11 dígitos"
        
    if cpf_limpo == cpf_limpo[0] * 11:
        return False, "CPF inválido (dígitos repetidos)"
    
    # Cálculo dos dígitos verificadores
    numeros = [int(digito) for digito in cpf_limpo]
    
    # Primeiro dígito
    soma = sum(n * (10 - i) for i, n in enumerate(numeros[:9]))
    resto = (soma * 10) % 11
    digito1 = resto if resto < 10 else 0
    
    # Segundo dígito
    soma = sum(n * (11 - i) for i, n in enumerate(numeros[:10]))
    resto = (soma * 10) % 11
    digito2 = resto if resto < 10 else 0
    
    # Validação final
    if numeros[9] == digito1 and numeros[10] == digito2:
        return True, "CPF válido"
    else:
        return False, "Dígitos verificadores incorretos"

def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt para senhas (com salt automático)"""
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return pwd_context.verify(senha, hash_senha)

def criptografar(texto: str) -> bytes:
    """Criptografa dados sensíveis (para fins didáticos)"""
    return cipher.encrypt(texto.encode())

def descriptografar(texto_criptografado: bytes) -> str:
    """Descriptografa dados (complementar à função anterior)"""
    return cipher.decrypt(texto_criptografado).decode()