import pytest
from contextual_enrichment import aplicar_regra_001_heranca_contratante

# Sample blocks derived from earlier investigation
BLOCK_PREV_A = """
sistema
informatizado ... Contratante: O Município de Teresópolis através da Secretaria Municipal de Educação. Contratada: Prime Consultoria.
"""

BLOCK_CURR_A = """
termo aditivo ao Contrato n.º 008.009.2025, ... Processo n° 1.438/2025.
PELO CONTRATANTE: CARLA RABELLO FERREIRA.
PELA CONTRATADA: RENATA NUNES FERREIRA.
"""

METAS_PREV_A = {'contrato': '008.009.2025', 'processo': None, 'contratante': 'O Município de Teresópolis através da Secretaria Municipal de Educação.'}
METAS_CURR_A = {'contrato': '008.009.2025', 'processo': '1.438/2025', 'contratante': None}


def test_case_A_herda_contratante():
    updated, applied, audit = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_A, METAS_PREV_A, 3,
        BLOCK_CURR_A, METAS_CURR_A, 4,
        'dummy.pdf'
    )

    assert applied is True
    assert updated['contratante'] == METAS_PREV_A['contratante']
    assert audit is not None


# Case B: contratos diferentes -> não herdar
BLOCK_PREV_B = "Contratante: O Município de X."
BLOCK_CURR_B = "Termo aditivo ao Contrato n.º 999.999.9999. PELO CONTRATANTE: Fulano."
METAS_PREV_B = {'contrato': '001.001.2020', 'processo': None, 'contratante': 'O Município de X.'}
METAS_CURR_B = {'contrato': '999.999.9999', 'processo': None, 'contratante': None}

def test_case_B_nao_herda_por_contrato_diferente():
    updated, applied, audit = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_B, METAS_PREV_B, 5,
        BLOCK_CURR_B, METAS_CURR_B, 6,
        'dummy.pdf'
    )
    assert applied is False
    assert updated['contratante'] is None

# Case C: mesmo processo -> herdar
BLOCK_PREV_C = "Contratante: O Município de X."
BLOCK_CURR_C = "Termo ... Processo n° 123/2025. PELO CONTRATANTE: Fulano."
METAS_PREV_C = {'contrato': None, 'processo': '123/2025', 'contratante': 'O Município de X.'}
METAS_CURR_C = {'contrato': None, 'processo': '123/2025', 'contratante': None}

def test_case_C_herda_por_processo():
    updated, applied, audit = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_C, METAS_PREV_C, 10,
        BLOCK_CURR_C, METAS_CURR_C, 11,
        'dummy.pdf'
    )
    assert applied is True
    assert updated['contratante'] == METAS_PREV_C['contratante']

# Case D: prev only boilerplate -> não herdar
BLOCK_PREV_D = "DIÁRIO OFICIAL ... Contratante:"
BLOCK_CURR_D = "Termo aditivo ... PELO CONTRATANTE: Fulano."
METAS_PREV_D = {'contrato': None, 'processo': None, 'contratante': None}
METAS_CURR_D = {'contrato': None, 'processo': None, 'contratante': None}

def test_case_D_nao_herda_boilerplate():
    updated, applied, audit = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_D, METAS_PREV_D, 20,
        BLOCK_CURR_D, METAS_CURR_D, 21,
        'dummy.pdf'
    )
    assert applied is False

# Case E: apostilamento -> herdar
BLOCK_PREV_E = "Contratante: O Município. Contrato n.º 007.007.2025"
BLOCK_CURR_E = "1º Termo Aditivo ao Contrato n° 007.007.2025. PELO CONTRATANTE: Fulano."
METAS_PREV_E = {'contrato': '007.007.2025', 'processo': None, 'contratante': 'O Município.'}
METAS_CURR_E = {'contrato': '007.007.2025', 'processo': None, 'contratante': None}

def test_case_E_herda_apostilamento():
    updated, applied, audit = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_E, METAS_PREV_E, 2,
        BLOCK_CURR_E, METAS_CURR_E, 3,
        'dummy.pdf'
    )
    assert applied is True

# Case F: idempotência
def test_case_F_idempotencia():
    updated1, applied1, audit1 = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_A, METAS_PREV_A, 3,
        BLOCK_CURR_A, METAS_CURR_A, 4,
        'dummy.pdf'
    )
    updated2, applied2, audit2 = aplicar_regra_001_heranca_contratante(
        BLOCK_PREV_A, updated1, 3,
        BLOCK_CURR_A, updated1, 4,
        'dummy.pdf'
    )
    assert applied1 is True
    assert applied2 is False or updated2['contratante'] == updated1['contratante']
