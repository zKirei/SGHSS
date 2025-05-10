# core/utils.py
import re

def formatar_cpf(cpf: str) -> str:
    """Formata CPF no padrão XXX.XXX.XXX-XX"""
    cpf_limpo = re.sub(r'\D', '', cpf)
    return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}" if len(cpf_limpo) == 11 else cpf

def formatar_telefone(telefone: str) -> str:
    """Formata telefone no padrão (XX) XXXXX-XXXX"""
    nums = re.sub(r'\D', '', telefone)
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return telefone