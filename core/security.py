from passlib.context import CryptContext
import re
from cryptography.fernet import Fernet

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
KEY = Fernet.generate_key()
cipher = Fernet(KEY)

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_senha: str) -> bool:
    return pwd_context.verify(senha, hash_senha)

import re

import re

def sanitizar_input(input_str: str) -> str:
    """Sanitização robusta contra SQLi e XSS"""
    if not input_str:
        return input_str
    
    # 1. Remoção de tags HTML/JS e conteúdo
    input_str = re.sub(r'<[^>]*>', '', input_str)
    
    # 2. Remoção de comandos SQL e padrões perigosos
    padroes_perigosos = [
        r'\b(DROP|DELETE|INSERT|ALTER)\s+(\w+\s+){1,3}',  # Comandos DDL/DML
        r';|\-\-|/\*|\*/|\\',                             # Caracteres especiais
        r"'",                                             # Quebra de strings
        r'\b(OR|AND)\s+\d+=\d+'                           # Condições sempre verdadeiras
    ]
    
    for padrao in padroes_perigosos:
        input_str = re.sub(padrao, '', input_str, flags=re.IGNORECASE)
    
    # 3. Normalização final
    input_str = " ".join(input_str.split())
    return input_str.strip()

def criptografar(texto: str) -> bytes:
    return cipher.encrypt(texto.encode())

def descriptografar(texto_criptografado: bytes) -> str:
    return cipher.decrypt(texto_criptografado).decode()

def validar_cpf(cpf: str) -> bool:
    # Implementação do algoritmo de validação de CPF
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    # ... (código completo da validação)
    return True