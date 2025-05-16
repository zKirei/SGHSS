# core/security.py (versão corrigida e unificada)
from passlib.context import CryptContext
import re
import bleach
from cryptography.fernet import Fernet
from typing import Tuple

# Configurações de segurança
CHAVE_FIXA = Fernet.generate_key()  # Em produção, armazene de forma segura!
cipher = Fernet(CHAVE_FIXA)
pwd_context = CryptContext(schemes=['bcrypt', 'sha256_crypt'], deprecated='auto')

# ----------------------------------------------
# Funções de Sanitização e Validação
# ----------------------------------------------

def sanitizar_input(input_str: str) -> str:
    # Remove tags HTML
    cleaned = bleach.clean(input_str, tags=[], attributes={}, strip=True)
    
    # Remove comandos SQL e caracteres perigosos
    cleaned = re.sub(
        r'\b(DROP|DELETE|INSERT|ALTER|EXEC|OR|SELECT|UPDATE)\b|[;\'"()=#-]',
        '', 
        cleaned,
        flags=re.IGNORECASE
    )
    
    # Normaliza espaços
    return re.sub(r'\s+', ' ', cleaned).strip()[:500]

# ----------------------------------------------
# Validação de CPF
# ----------------------------------------------
def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Validação rigorosa de CPF com retorno detalhado.
    - Verifica formato, dígitos repetidos e cálculo matemático.
    - Aceita CPFs formatados ou não.
    """
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Verificação básica
    if len(cpf_limpo) != 11:
        return (False, "CPF deve conter 11 dígitos")
        
    if cpf_limpo == cpf_limpo[0] * 11:
        return (False, "CPF inválido (dígitos repetidos)")
    
    # Conversão para inteiros
    try:
        numeros = [int(digito) for digito in cpf_limpo]
    except ValueError:
        return (False, "CPF contém caracteres inválidos")

    # Cálculo dos dígitos verificadores
    soma = sum(numeros[i] * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = d1 if d1 < 10 else 0
    
    soma = sum(numeros[i] * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = d2 if d2 < 10 else 0

    # Validação final
    if numeros[9] != d1 or numeros[10] != d2:
        return (False, "Dígitos verificadores inválidos")
    
    return (True, "CPF válido")

def validar_telefone(telefone: str) -> Tuple[bool, str]:
    """Valida telefone brasileiro com DDD"""
    padrao = r"^(\+?55)?(0?[1-9]{2})?(9?\d{4}[-\.]?\d{4})$"
    telefone_limpo = re.sub(r'\D', '', telefone)
    
    if len(telefone_limpo) not in (10, 11):
        return (False, "Número deve ter 10 ou 11 dígitos")
    
    if not re.fullmatch(padrao, telefone_limpo):
        return (False, "Formato inválido")
    
    return (True, "Número válido")

# ----------------------------------------------
# Funções de Criptografia
# ----------------------------------------------
def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt com salt aleatório"""
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