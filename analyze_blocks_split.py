from extractor import extrair_texto
from parser import segmentar_publicacoes, extrair_contrato, extrair_processo, identificar_tipo

PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"

full_text = extrair_texto(PDF_PATH)
blocks = segmentar_publicacoes(full_text)

occurrences = []

import re
for i, block in enumerate(blocks):
    b_lower = block.lower()
    has_pelo = re.search(r'\bpelo\s+contratante\b', block, flags=re.IGNORECASE) is not None
    # institutional label: word 'contratante' followed by optional spaces and a colon
    has_institutional_contratante = re.search(r'\bcontratante\s*:', block, flags=re.IGNORECASE) is not None
    if has_pelo and not has_institutional_contratante:
        prev = blocks[i-1] if i-1 >=0 else None
        prev_has_contratante = False
        match_prev = False
        reason = ''
        if prev:
            prev_has_contratante = 'contratante:' in prev.lower()
            # extract contract/process from both
            c_this = extrair_contrato(block)
            p_this = extrair_processo(block)
            c_prev = extrair_contrato(prev)
            p_prev = extrair_processo(prev)
            if c_this and c_prev and c_this == c_prev:
                match_prev = True
                reason = 'contract equal'
            elif p_this and p_prev and p_this == p_prev:
                match_prev = True
                reason = 'process equal'
            else:
                # if previous contains same contract number textually
                if c_prev and c_prev == c_this:
                    match_prev = True
                    reason = 'contract textual equal'
        occurrences.append({
            'index': i+1,
            'has_pelo': has_pelo,
            'has_contratante': has_contratante,
            'prev_index': i if i>=1 else None,
            'prev_has_contratante': prev_has_contratante,
            'match_prev': match_prev,
            'reason': reason,
            'contract_this': extrair_contrato(block),
            'process_this': extrair_processo(block),
            'contract_prev': extrair_contrato(prev) if prev else None,
            'process_prev': extrair_processo(prev) if prev else None,
            'snippet_prev_last200': prev[-200:] if prev else None,
            'snippet_this_first200': block[:200],
            'snippet_this_last200': block[-200:],
        })

# total of blocks that are contracts/aditivo/apostilamento
types_of_interest = {'contrato','aditivo','apostilamento','extrato'}
count_interest = 0
for block in blocks:
    if identificar_tipo(block) in types_of_interest:
        count_interest += 1

# prepare report
print('Total blocks:', len(blocks))
print('Total blocks of interest (contrato/aditivo/apostilamento/extrato):', count_interest)
print('Occurrences where block contains PELO CONTRATANTE but not Contratante:')
print('Count:', len(occurrences))
print('Percentage vs blocks of interest: {:.2f}%'.format((len(occurrences)/count_interest*100) if count_interest>0 else 0))

# show up to 8 examples
print('\nExamples (up to 8):')
for ex in occurrences[:8]:
    print('\n--- Example Block', ex['index'], '---')
    print('Prev block index:', ex['prev_index'])
    print('Prev has Contratante?:', ex['prev_has_contratante'])
    print('Match prev by contract/process?:', ex['match_prev'], ex['reason'])
    print('contract_this:', ex['contract_this'])
    print('process_this:', ex['process_this'])
    print('contract_prev:', ex['contract_prev'])
    print('process_prev:', ex['process_prev'])
    print('\nSnippet prev (last 200 chars):\n')
    print(ex['snippet_prev_last200'])
    print('\nSnippet this (first 200 chars):\n')
    print(ex['snippet_this_first200'])

# evidence of division: count where prev_has_contratante and match_prev True
evidence_count = sum(1 for ex in occurrences if ex['prev_has_contratante'] and ex['match_prev'])
print('\nEvidence count where previous block contains Contratante and contract/process matched:', evidence_count)

# list indices where evidence true
evidence_indices = [ex['index'] for ex in occurrences if ex['prev_has_contratante'] and ex['match_prev']]
print('Indices with evidence of split:', evidence_indices)

# If none matched by contract/process still show those where prev_has_contratante
simple_prev_has = [ex['index'] for ex in occurrences if ex['prev_has_contratante']]
print('Indices where previous contains Contratante irrespective of contract/process match:', simple_prev_has)
