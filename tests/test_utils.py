# tests/test_utils.py
import pytest
from core.security import validar_cpf, validar_telefone

def test_cpf_valido():
    assert validar_cpf("529.982.247-25")[0] == True

def test_cpf_invalido():
    assert validar_cpf("111.111.111-11")[0] == False

def test_telefone_valido():
    assert validar_telefone("(11) 99999-8888")[0] == True

def test_telefone_invalido():
    assert validar_telefone("1234")[0] == False