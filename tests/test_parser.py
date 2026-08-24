import pytest

from parser import (
    extrair_processo,
    identificar_tipo,
    extrair_contrato,
    extrair_fornecedor,
    extrair_contratante,
    extrair_cnpj,
    extrair_valor_principal,
    extrair_objeto,
    extrair_vigencia,
    segmentar_publicacoes,
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


def test_protocolo_nao_e_processo():

    texto = """
    Protocolo nº 32.481/2025
    """

    assert extrair_processo(texto) is None


def test_memorando_nao_e_processo():

    texto = """
    Prazo: 30 (trinta) dias.

    Memorando n° 29.744/25.

    PELO CONTRATANTE
    """

    assert extrair_processo(texto) is None


def test_processo_sem_numero():

    texto = """
    Processo nº
    """

    assert extrair_processo(texto) is None


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Processo nº 214.400-6/2025", "214.400-6/2025"),
        (
            "Processo Administrativo nº 04105.0000001409/2024",
            "04105.0000001409/2024",
        ),
        (
            "Processo nº 63386.000421/2025-30",
            "63386.000421/2025-30",
        ),
        ("Processo Administrativo nº 8.575 /2025", "8.575/2025"),
    ],
)
def test_processo_preserva_formatos_administrativos_reais(texto, esperado):
    assert extrair_processo(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Contrato nº 083.11.2021",
        "Contrato nº 008.014.2026",
        "conforme protocolo nº 52/26",
    ],
)
def test_processo_exige_contexto_de_processo(texto):
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

def test_extrair_contrato_registrado_publicado():
    texto = """
    Termo Aditivo tem por objeto o reequilíbrio financeiro do Contrato registrado e
    publicado sob o nº. 005.013.2025, na forma abaixo, conforme consta do Processo
    Administrativo nº 733/2025.
    """

    assert extrair_contrato(texto) == "005.013.2025"


def test_extrair_contrato_termo_cessao_uso():
    texto = """
    1º Termo Aditivo ao Termo de Cessão de Uso de Imóvel 010.000.2024

    Cedente: Município de Teresópolis.

    Objeto: alteração do Termo de Cessão de Uso de Bem Imóvel registrado sob o nº
    010.000.2024.
    """

    assert extrair_contrato(texto) == "010.000.2024"

def test_extrair_objeto_sem_dois_pontos():
    texto = """
    3º Termo de Apostilamento ao Contrato nº 020.06.2016

    Contratada: AADL Empreendimento e Participações Ltda.

    Objeto
    Adequação orçamentária do contrato, por parte da Administração,
    a fim de que conste o empenho nº 492/2026 para o exercício
    financeiro atual, no valor de R$ 19.412,28.
    """

    esperado = (
        "Adequação orçamentária do contrato, por parte da Administração, "
        "a fim de que conste o empenho nº 492/2026 para o exercício "
        "financeiro atual, no valor de R$ 19.412,28"
    )

    assert extrair_objeto(texto) == esperado

# =====================================================
# TESTES - EXTRAÇÃO DE FORNECEDOR
# =====================================================

def test_fornecedor_contratada():

    texto = """
    CONTRATADA: EMPRESA XPTO LTDA

    CNPJ: 12.345.678/0001-99
    """

    assert extrair_fornecedor(texto) == "EMPRESA XPTO LTDA"

def test_fornecedor_contratada_entidade_publica():
    texto = """
    CONTRATADA: Fundo Municipal dos Direitos da Criança e do adolescente.
    """

    assert (
        extrair_fornecedor(texto)
        == "Fundo Municipal dos Direitos da Criança e do adolescente"
    )

def test_fornecedor_caso_real_833():
    texto = """
    9° Termo Aditivo ao Contrato n°009.008.2025
    Contrato n° 009.008.2025 (A aquisição de materiais de almoxarifado e higiene para o
    Fundo Municipal de Assistência Social.).Contratante: O Município de Teresópolis através
    da Secretaria Assistência Social e Direitos Humanos. Contratada: Fundo Municipal
    dos Direitos da Criança e do adolescente . - Objeto: Presente termo Aditivo
    rerratificação da tabela . Valor R$: 35.428,96 (trinta e cinco mil, quatrocentos e vinte e
    oito reais e noventa e seis centavos). Processo n° 2.244/2025.
    PELO CONTRATANTE: MARIA DAS GRAÇAS GRANITO DOS SANTOS
    PELA CONTRATADA: WERICON DE JESUS MATOS.
    """

    assert (
        extrair_fornecedor(texto)
        == "Fundo Municipal dos Direitos da Criança e do adolescente"
    )

def test_fornecedor_ignora_representante_pela_contratada():
    texto = """
    PELA CONTRATADA: AMANDIO DO NASCIMENTO.
    """

    assert extrair_fornecedor(texto) is None

def test_fornecedor_ignora_orgao_publico():

    texto = """
    CONTRATADA: SECRETARIA MUNICIPAL DE SAÚDE

    CNPJ: 12.345.678/0001-99
    """

    assert extrair_fornecedor(texto) is None

def test_fornecedor_para_no_campo_objeto():

    texto = """
    CONTRATADA: EMPRESA XPTO LTDA

    OBJETO: Prestação de serviços de limpeza urbana.
    """

    assert extrair_fornecedor(texto) == "EMPRESA XPTO LTDA"

# =====================================================
# TESTES - EXTRAÇÃO DE CONTRATANTE
# =====================================================

def test_contratante():

    texto = """
    CONTRATANTE: Prefeitura Municipal de Teresópolis

    CNPJ: 29.138.369/0001-47
    """

    assert (
        extrair_contratante(texto)
        == "Prefeitura Municipal de Teresópolis"
    )

# =====================================================
# TESTES - EXTRAÇÃO DE CONTRATANTE
# =====================================================

def test_contratante():

    texto = """
    CONTRATANTE: Prefeitura Municipal de Teresópolis

    CNPJ: 29.138.369/0001-47
    """

    assert (
        extrair_contratante(texto)
        == "Prefeitura Municipal de Teresópolis"
    )


def test_contratante_para_no_campo_cnpj():

    texto = """
    CONTRATANTE: Prefeitura Municipal de Teresópolis

    CNPJ: 29.138.369/0001-47
    """

    assert (
        extrair_contratante(texto)
        == "Prefeitura Municipal de Teresópolis"
    )


def test_sem_contratante():

    texto = """
    Contrato Administrativo nº 021/2026

    Objeto: Prestação de serviços.
    """

    assert extrair_contratante(texto) is None

# =====================================================
# TESTES - EXTRAÇÃO DE CNPJ
# =====================================================

def test_cnpj():

    texto = """
    CNPJ: 12.345.678/0001-99
    """

    assert extrair_cnpj(texto) == "12.345.678/0001-99"


def test_sem_cnpj():

    texto = """
    Contrato Administrativo nº 021/2026
    """

    assert extrair_cnpj(texto) is None


def test_primeiro_cnpj():

    texto = """
    CONTRATANTE

    CNPJ: 11.111.111/0001-11

    CONTRATADA

    CNPJ: 22.222.222/0001-22
    """

    assert extrair_cnpj(texto) == "11.111.111/0001-11"

# =====================================================
# TESTES - EXTRAÇÃO DE VALOR PRINCIPAL
# =====================================================

def test_valor_global():

    texto = """
    VALOR GLOBAL: R$ 150.000,00
    """

    assert extrair_valor_principal(texto) == 150000.00


def test_valor_total():

    texto = """
    VALOR TOTAL: R$ 89.500,00
    """

    assert extrair_valor_principal(texto) == 89500.00


def test_valor_contratado():

    texto = """
    Valor contratado: R$ 1.250,50
    """

    assert extrair_valor_principal(texto) == 1250.50

def test_valor_unico_sem_contexto():

    texto = """
    O presente contrato possui o valor de
    R$ 12.500,00.
    """

    assert extrair_valor_principal(texto) == 12500.00


def test_dois_valores_sem_contexto_retorna_none():

    texto = """
    A empresa apresentou proposta de

    R$ 10.000,00

    Após negociação foi apresentado

    R$ 12.000,00
    """

    assert extrair_valor_principal(texto) is None

def test_valor_principal_inteiro_com_milhar():
    texto = """
    Valor R$: 1.168 (um mil, cento e sessenta e oito reais).
    """
    assert extrair_valor_principal(texto) == 1168.0

def test_valor_principal_inteiro():
    texto = """
    Valor R$: 5.000 (Cinco mil reais).
    """
    assert extrair_valor_principal(texto) == 5000.0

# =====================================================
# TESTES - EXTRAÇÃO DE OBJETO
# =====================================================

def test_objeto():

    texto = """
    OBJETO:
    Prestação de serviços especializados em tecnologia.

    VALOR GLOBAL:
    R$ 100.000,00
    """

    assert (
    extrair_objeto(texto)
    == "Prestação de serviços especializados em tecnologia"
)
    
# =====================================================
# TESTES - EXTRAÇÃO DE VIGÊNCIA
# =====================================================

def test_vigencia():

    texto = """
    VIGÊNCIA:
    12 meses.

    PROCESSO:
    12345/2026
    """

    assert extrair_vigencia(texto) == "12 meses"

# =====================================================
# TESTES - EXTRAÇÃO DE VIGÊNCIA
# =====================================================

def test_vigencia():

    texto = """
    VIGÊNCIA:
    12 meses.

    PROCESSO:
    12345/2026
    """

    assert extrair_vigencia(texto) == "12 meses"


def test_prazo():

    texto = """
    PRAZO:
    180 dias.

    VALOR GLOBAL:
    R$ 100.000,00
    """

    assert extrair_vigencia(texto) == "180 dias"


def test_prazo_contratual():

    texto = """
    PRAZO CONTRATUAL:
    24 meses.

    CONTRATANTE:
    Prefeitura Municipal
    """

    assert extrair_vigencia(texto) == "24 meses"


def test_sem_vigencia():

    texto = """
    Contrato Administrativo nº 021/2026

    Objeto: Prestação de serviços.
    """

    assert extrair_vigencia(texto) is None

# =====================================================
# TESTES - SEGMENTAÇÃO DE PUBLICAÇÕES
# =====================================================

def test_segmenta_dois_contratos():

    texto = """
    CONTRATO Nº 001/2026

    Objeto: Prestação de serviços especializados.

    Processo Administrativo nº 12345/2026.

    Valor Global: R$ 100.000,00.

    Vigência: 12 meses.

    CONTRATO Nº 002/2026

    Objeto: Aquisição de materiais de informática.

    Processo Administrativo nº 54321/2026.

    Valor Global: R$ 250.000,00.

    Vigência: 24 meses.
    """

    blocos = segmentar_publicacoes(texto)

    assert len(blocos) == 2

    assert "CONTRATO Nº 001/2026" in blocos[0]
    assert "CONTRATO Nº 002/2026" in blocos[1]

def test_segmentacao_nao_quebra_frase_continuada():

    texto = """
    PORTARIA GP Nº 311

    Art. 1º DESIGNAR os servidores a seguir relacionados para atuarem como gestor e fiscal no

    contrato celebrado por este Município e vinculado à Secretaria Municipal de Administração,
    conforme Memorando nº 10.706/2025:

    Processo
    Servidor
    Matrícula
    """

    blocos = segmentar_publicacoes(texto)

    assert len(blocos) == 1

def test_segmentacao_nao_quebra_cabecalho_de_tabela():

    texto = """
    PORTARIA GP Nº 311

    Art. 1º DESIGNAR os servidores para atuarem como gestor e fiscal.

    Contrato nº:
    Administrativo/
    Contratado(a):
    Objeto:
    Gestor/Fiscal:

    Art. 2º Os servidores designados...
    """

    blocos = segmentar_publicacoes(texto)

    assert len(blocos) == 1
