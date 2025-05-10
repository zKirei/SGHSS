# core/utils.py
import re
from typing import Tuple

def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """Valida CPF com tratamento de formatação e retorno detalhado"""
    # Remove caracteres não numéricos
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Verifica tamanho e dígitos repetidos
    if len(cpf_limpo) != 11:
        return False, "CPF deve conter 11 dígitos"
        
    if cpf_limpo == cpf_limpo[0] * 11:
        return False, "CPF inválido (dígitos repetidos)"
    
    # Converte para inteiro
    try:
        cpf_nums = list(map(int, cpf_limpo))
    except ValueError:
        return False, "CPF contém caracteres inválidos"

    # Cálculo do primeiro dígito verificador
    soma = sum(cpf_nums[i] * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto != cpf_nums[9]:
        return False, "Dígito verificador inválido"

    # Cálculo do segundo dígito verificador
    soma = sum(cpf_nums[i] * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto != cpf_nums[10]:
        return False, "Dígito verificador inválido"

    return True, "CPF válido"

def formatar_cpf(cpf: str) -> str:
    """Formata CPF no padrão XXX.XXX.XXX-XX"""
    cpf_limpo = re.sub(r'\D', '', cpf)
    return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}" if len(cpf_limpo) == 11 else cpf

def validar_telefone(telefone: str) -> Tuple[bool, str]:
    """Valida telefone brasileiro com DDD"""
    padrao = r"^(\+?55)?(0?[1-9]{2})?(9?\d{4}[-\.]?\d{4})$"
    telefone_limpo = re.sub(r'\D', '', telefone)
    
    if len(telefone_limpo) not in (10, 11):
        return False, "Número deve ter 10 ou 11 dígitos"
    
    if not re.fullmatch(padrao, telefone_limpo):
        return False, "Formato inválido"
    
    return True, "Número válido"

def formatar_telefone(telefone: str) -> str:
    """Formata telefone no padrão (XX) XXXXX-XXXX"""
    nums = re.sub(r'\D', '', telefone)
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return telefone