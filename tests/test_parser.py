import pytest

from parser import (
    extrair_processo,
    identificar_tipo,
    extrair_contrato,
)


# =====================================================
# TESTES - EXTRAÇÃO DE PROCESSO
# =====================================================

def test_processo_administrativo():

    texto = """
    Processo Administrativo nº 11.302/2025
    """

    assert extrair_processo(texto) == "11.302/2025"


def test_processo_abreviado():

    texto = """
    Proc. nº 12345/2026
    """

    assert extrair_processo(texto) == "12345/2026"


def test_protocolo():

    texto = """
    Protocolo nº 32.481/2025
    """

    assert extrair_processo(texto) == "32.481/2025"


def test_memorando():

    texto = """
    Prazo: 30 (trinta) dias.

    Memorando n° 29.744/25.

    PELO CONTRATANTE
    """

    assert extrair_processo(texto) == "29.744/25"


def test_processo_sem_numero():

    texto = """
    Processo nº
    """

    assert extrair_processo(texto) is None


def test_sem_referencia():

    texto = """
    Contrato de Prestação de Serviços
    """

    assert extrair_processo(texto) is None


# =====================================================
# TESTES - IDENTIFICAÇÃO DOCUMENTAL
# =====================================================

def test_identifica_contrato():

    texto = """
    CONTRATO Nº 021.012.2025

    Contratante:
    """

    assert identificar_tipo(texto) == "contrato"


def test_identifica_apostilamento():

    texto = """
    3º Termo de Apostilamento ao Contrato nº 021.012.2025
    """

    assert identificar_tipo(texto) == "apostilamento"


def test_identifica_aditivo():

    texto = """
    2º Termo Aditivo ao Contrato nº 021.012.2025
    """

    assert identificar_tipo(texto) == "aditivo"


def test_identifica_portaria():

    texto = """
    PORTARIA GP Nº 123/2026
    """

    assert identificar_tipo(texto) == "portaria"


def test_identifica_extrato():

    texto = """
    EXTRATO DE CONTRATO
    """

    assert identificar_tipo(texto) == "extrato"


# =====================================================
# TESTES - EXTRAÇÃO DE CONTRATO
# =====================================================

def test_contrato():

    texto = """
    Contrato nº 021.012.2025
    """

    assert extrair_contrato(texto) == "021.012.2025"


def test_extrato_contrato():

    texto = """
    Extrato de Contrato nº 003.005.2026
    """

    assert extrair_contrato(texto) == "003.005.2026"


def test_termo_apostilamento():

    texto = """
    5º Termo de Apostilamento ao Contrato nº 021.012.2025
    """

    assert extrair_contrato(texto) == "021.012.2025"


def test_sem_contrato():

    texto = """
    Portaria GP nº 123/2026
    """

    assert extrair_contrato(texto) is None

def test_termo_colaboracao():

    texto = """
    Termo de Colaboração nº 001.008.2025
    """

    assert extrair_contrato(texto) == "001.008.2025"


def test_termo_autorizacao():

    texto = """
    Termo de Autorização de Uso nº 011.001.2025
    """

    assert extrair_contrato(texto) == "011.001.2025"


def test_contrato_locacao():

    texto = """
    Contrato de Locação nº 022.CL.05.2022
    """

    assert extrair_contrato(texto) == "022.CL.05.2022"