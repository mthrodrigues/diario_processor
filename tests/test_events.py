from events import extrair_eventos_bloco
from main import _timeline_vinculo_valido
from taxonomy.event_taxonomy import (
    DESIGNACAO_FISCAL,
    CONTRATACAO,
    NOMEACAO,
    EXONERACAO
)


def test_designacao_fiscal_reutiliza_contrato_dos_metadados():

    texto = """
    PORTARIA Nº 001/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato de Locação nº 022.CL.05.2022.
    """

    metadados = {
        "tipo": "portaria",
        "contrato": "022.CL.05.2022",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == DESIGNACAO_FISCAL
    )

    assert evento["contrato"] == "022.CL.05.2022"


def test_segmenta_duas_portarias_em_dois_subeventos():

    texto = """
    PORTARIA GP Nº 469/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato nº 001/2026.

    Processo nº 100/2026.

    PORTARIA GP Nº 470/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato nº 002/2026.

    Processo nº 200/2026.
    """

    metadados = {
        "tipo": "portaria",
        "contrato": "001/2026",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 2


def test_contratacao_utiliza_metadados_do_parser():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026

    Objeto: Prestação de serviços especializados.
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": "Prefeitura Municipal de Teresópolis",
        "fornecedor_normalizado": "Empresa XPTO LTDA",
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == CONTRATACAO
    )

    assert evento["entidade_origem"]["nome"] == \
        "Prefeitura Municipal de Teresópolis"

    assert evento["entidade_destino"]["nome"] == \
        "Empresa XPTO LTDA"

    assert evento["contrato"] == "015/2026"
    assert evento["processo"] == "12345/2026"
    assert evento["valor"] == 250000.00
    assert evento["objeto"] == "Prestação de serviços especializados"

def test_contratacao_nao_gera_evento_sem_fornecedor():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": "Prefeitura Municipal de Teresópolis",
        "fornecedor_normalizado": None,
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert eventos == []

def test_contratacao_nao_gera_evento_sem_contratante():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": None,
        "fornecedor_normalizado": "Empresa XPTO LTDA",
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert eventos == []

def test_nomeacao_gera_evento_com_agente_cargo_e_orgao():

    texto = """
    PORTARIA Nº 100/2026

    NOMEAR JOÃO DA SILVA para exercer o Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na Secretaria
    Municipal de Administração.
    """

    metadados = {
        "tipo": "portaria",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == NOMEACAO
    )

    assert evento["agente"]["nome"] == "JOÃO DA SILVA"
    assert evento["cargo"] == "Diretor de Compras"
    assert evento["orgao"] == "Secretaria Municipal de Administração"

def test_exoneracao_gera_evento_com_agente_cargo_e_orgao():

    texto = """
    PORTARIA Nº 101/2026

    EXONERAR JOÃO DA SILVA do Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na
    Secretaria Municipal de Administração.
    """

    metadados = {
        "tipo": "portaria",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == EXONERACAO
    )

    assert evento["agente"]["nome"] == "JOÃO DA SILVA"
    assert evento["cargo"] == "Diretor de Compras"
    assert evento["orgao"] == "Secretaria Municipal de Administração"


def test_timeline_vinculo_requer_pessoa_e_orgao():
    assert _timeline_vinculo_valido(NOMEACAO, None, None) is False
    assert _timeline_vinculo_valido(NOMEACAO, 10, None) is False
    assert _timeline_vinculo_valido(NOMEACAO, None, 20) is False
    assert _timeline_vinculo_valido(NOMEACAO, 10, 20) is True
    assert _timeline_vinculo_valido(EXONERACAO, 10, 20) is True
    assert _timeline_vinculo_valido(DESIGNACAO_FISCAL, 10, 20) is False