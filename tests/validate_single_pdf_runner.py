import json
from extractor import extrair_texto
from parser import segmentar_publicacoes
from processor import extrair_metadados_bloco
from contextual_enrichment import aplicar_regra_001_heranca_contratante

PDF_PATH = r'C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf'

def main():
    texto = extrair_texto(PDF_PATH)
    blocks = segmentar_publicacoes(texto)
    metadados_before = [extrair_metadados_bloco(b) for b in blocks]

    previous_block = None
    previous_metadados = None
    previous_num = None
    metadados_after = []

    for i, bloco in enumerate(blocks, start=1):
        curr_meta = metadados_before[i-1].copy()
        updated_meta, applied, audit = aplicar_regra_001_heranca_contratante(
            previous_block, previous_metadados, previous_num,
            bloco, curr_meta, i, PDF_PATH
        )
        metadados_after.append((updated_meta, applied, audit))
        previous_block = bloco
        previous_metadados = updated_meta
        previous_num = i

    idx = 4 - 1
    before = metadados_before[idx]
    after, applied_flag, audit = metadados_after[idx]

    # Debug: show contrato/processo/contratante for prev and curr
    prev_meta = metadados_before[idx-1]
    curr_meta = metadados_before[idx]
    print('Prev meta (contrato/processo/contratante):', prev_meta.get('contrato'), prev_meta.get('processo'), prev_meta.get('contratante'))
    print('Curr meta (contrato/processo/contratante):', curr_meta.get('contrato'), curr_meta.get('processo'), curr_meta.get('contratante'))

    print('\nApplied flag:', applied_flag)
    print('Audit:', json.dumps(audit, ensure_ascii=False, indent=2))

    changed = []
    for k in sorted(set(list(before.keys()) + list(after.keys()))):
        b = before.get(k)
        a = after.get(k)
        if b != a:
            changed.append((k, b, a))

    print('\nChanged fields:')
    if not changed:
        print('  None')
    for k, b, a in changed:
        print('-', k)
        print('  before:', b)
        print('  after: ', a)

    texto_persisted = blocks[idx]
    print('\nTexto bloco length:', len(texto_persisted))

    for j in (idx-1, idx):
        snippet = blocks[j]
        print(f"\nBlock {j+1} start (first 200 chars):\n{snippet[:200]!r}")
        print('  has Contratante:', 'Contratante' in snippet)
        print('  has PELO CONTRATANTE:', 'PELO CONTRATANTE' in snippet)

if __name__ == '__main__':
    main()
