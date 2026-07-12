from events import extrair_eventos_bloco
from taxonomy.event_taxonomy import DESIGNACAO_FISCAL


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

    print(eventos)

    assert len(eventos) == 2