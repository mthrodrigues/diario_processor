from extractor import extrair_texto
from parser import segmentar_publicacoes, extrair_contrato, extrair_processo, identificar_tipo
import re

PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"
full_text = extrair_texto(PDF_PATH)
blocks = segmentar_publicacoes(full_text)

types_of_interest = {'contrato','aditivo','apostilamento','extrato'}
count_interest = sum(1 for b in blocks if identificar_tipo(b) in types_of_interest)

results = []
for i, b in enumerate(blocks):
    has_pelo = re.search(r'\bpelo\s+contratante\b', b, flags=re.IGNORECASE) is not None
    # institutional label = 'Contratante:' not immediately preceded by 'Pelo ' or 'Pela '
    has_institutional = re.search(r'(?i)(?<!pelo )(?<!pela )\bcontratante\s*:', b) is not None
    if has_pelo and not has_institutional:
        prev = blocks[i-1] if i>=1 else None
        prev_has_institutional = False
        match_prev = False
        reason = ''
        if prev:
            prev_has_institutional = re.search(r'\bcontratante\s*:', prev, flags=re.IGNORECASE) is not None
            c_this = extrair_contrato(b)
            p_this = extrair_processo(b)
            c_prev = extrair_contrato(prev)
            p_prev = extrair_processo(prev)
            if c_this and c_prev and c_this == c_prev:
                match_prev = True
                reason = 'contract equal'
            elif p_this and p_prev and p_this == p_prev:
                match_prev = True
                reason = 'process equal'
        results.append((i+1, prev is not None and (i), prev_has_institutional, match_prev, reason, c_prev, c_this, p_prev, p_this, prev[-200:] if prev else None, b[:200]))

# report
print('total blocks:', len(blocks))
print('blocks of interest count:', count_interest)
print('matches where block has PELO CONTRATANTE but not institutional CONTRATANTE:', len(results))

for r in results:
    idx, prev_idx, prev_has_inst, match_prev, reason, c_prev, c_this, p_prev, p_this, prev_tail, this_head = r
    print('\n--- Block', idx, '---')
    print('prev index:', prev_idx)
    print('prev_has_institutional?:', prev_has_inst)
    print('match_prev:', match_prev, reason)
    print('contract_prev:', c_prev)
    print('contract_this:', c_this)
    print('process_prev:', p_prev)
    print('process_this:', p_this)
    print('\nprev_tail:')
    print(prev_tail)
    print('\nthis_head:')
    print(this_head)

# compute percentage vs blocks of interest
percent = (len(results)/count_interest*100) if count_interest>0 else 0
print('\npercentage vs blocks of interest: {:.2f}%'.format(percent))

# also list blocks where prev_has_institutional true
prev_has_list = [r[0] for r in results if r[2]]
print('\nblocks where previous block contains institutional CONTRATANTE:', prev_has_list)
