import os
from extractor import extrair_texto
from parser import segmentar_publicacoes
from processor import extrair_metadados_bloco
from contextual_enrichment import aplicar_regra_001_heranca_contratante

# Use one of the five real PDFs identified during investigation
PDF_PATH = os.path.join('C:\\automacoes\\diario_bot\\pdfs\\2026\\06\\diario_3375.pdf')


def test_integration_enrichment_diario_3375():
    texto = extrair_texto(PDF_PATH)
    blocks = segmentar_publicacoes(texto)

    # we expect at least 4 blocks based on earlier analysis
    assert len(blocks) >= 4

    # extract metadados for all blocks first
    metadados_before = [extrair_metadados_bloco(b) for b in blocks]

    # simulate main pipeline with EC applied
    previous_block = None
    previous_metadados = None
    previous_num = None

    metadados_after = []

    for i, bloco in enumerate(blocks, start=1):
        curr_meta = metadados_before[i - 1].copy()

        updated_meta, applied, audit = aplicar_regra_001_heranca_contratante(
            previous_block,
            previous_metadados,
            previous_num,
            bloco,
            curr_meta,
            i,
            PDF_PATH,
        )

        metadados_after.append((updated_meta, applied, audit))

        # move previous
        previous_block = bloco
        previous_metadados = updated_meta
        previous_num = i

    # Identify the problematic block (block 4 expected)
    idx = 4 - 1
    before = metadados_before[idx]
    after, applied_flag, audit = metadados_after[idx]

    # Confirm only 'contratante' and 'contratante_normalizado' changed between before and after (if EC applied)
    for key in before.keys():
        if key == 'contratante':
            # if the rule applied, contratante should be the one from previous block
            if applied_flag:
                prev_contratante = metadados_after[idx - 1][0]['contratante'] if idx - 1 >= 0 else None
                assert after['contratante'] == prev_contratante
            else:
                # if not applied, it should remain the same
                assert after['contratante'] == before['contratante']
        elif key == 'contratante_normalizado':
            # contratante_normalizado should be recalculated only if EC applied
            if applied_flag:
                from normalizer import normalize_contratante
                expected_normalized = normalize_contratante(after['contratante'])
                assert after['contratante_normalizado'] == expected_normalized
            else:
                # if not applied, it should remain the same
                assert after['contratante_normalizado'] == before['contratante_normalizado']
        else:
            assert after[key] == before[key]
