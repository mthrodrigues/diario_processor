import csv
import json
import os
from extractor import extrair_texto
from parser import segmentar_publicacoes, extrair_contrato, extrair_processo, identificar_tipo
from database import conectar as db_conectar

CSV_IN = os.path.join(os.getcwd(), 'split_segmentation_report.csv')
TXT_OUT = os.path.join(os.getcwd(), 'split_segmentation_comparative_report.txt')
JSON_OUT = os.path.join(os.getcwd(), 'split_segmentation_comparative.json')

cases = []

# Load CSV
with open(CSV_IN, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cases.append(row)

# Try DB connection
db_conn = None
try:
    db_conn = db_conectar()
    db_cursor = db_conn.cursor()
except Exception:
    db_conn = None

results = []

for idx, case in enumerate(cases, 1):
    pdf = case['pdf_path']
    block_index = int(case['block_index']) if case['block_index'] else None
    prev_index = int(case['previous_block_index']) if case['previous_block_index'] else None

    entry = {
        'case_number': idx,
        'pdf_path': pdf,
        'publication_type': case.get('publication_type'),
        'block_index': block_index,
        'previous_block_index': prev_index,
        'contract_number_previous': case.get('contract_number_previous'),
        'contract_number_current': case.get('contract_number_current'),
        'process_previous': case.get('process_previous'),
        'process_current': case.get('process_current'),
        'has_institutional_contratante_previous': case.get('has_institutional_contratante_previous') == 'True' or case.get('has_institutional_contratante_previous') == '1',
        'has_institutional_contratante_current': case.get('has_institutional_contratante_current') == 'True' or case.get('has_institutional_contratante_current') == '1',
        'has_pelo_contratante_current': case.get('has_pelo_contratante_current') == 'True' or case.get('has_pelo_contratante_current') == '1',
        'persisted_block_match': None,
        'prev_block_text': None,
        'current_block_text': None,
        'prev_block_tail_500': None,
        'current_block_head_500': None,
        'persisted_textblock': None,
    }

    try:
        full_text = extrair_texto(pdf)
        blocks = segmentar_publicacoes(full_text)
    except Exception as e:
        entry['error'] = f'extraction/segmentation error: {e}'
        results.append(entry)
        continue

    # fetch previous block and current block if present
    try:
        if prev_index and 1 <= prev_index <= len(blocks):
            prev_block = blocks[prev_index-1]
            entry['prev_block_text'] = prev_block
            entry['prev_block_tail_500'] = prev_block[-500:]
            entry['prev_has_institutional'] = bool(prev_block and ('Contratante:' in prev_block or 'CONTRATANTE:' in prev_block.upper()))
        else:
            entry['prev_block_text'] = None
    except Exception as e:
        entry['prev_error'] = str(e)

    try:
        if block_index and 1 <= block_index <= len(blocks):
            curr_block = blocks[block_index-1]
            entry['current_block_text'] = curr_block
            entry['current_block_head_500'] = curr_block[:500]
            entry['current_has_pelo_contratante'] = bool(curr_block and ('PELO CONTRATANTE' in curr_block.upper() or 'Pelo Contratante' in curr_block))
            entry['current_has_institutional'] = bool(curr_block and ('Contratante:' in curr_block or 'CONTRATANTE:' in curr_block.upper()))
        else:
            entry['current_block_text'] = None
    except Exception as e:
        entry['current_error'] = str(e)

    # persisted block lookup
    if db_conn:
        try:
            db_cursor.execute('SELECT id, texto_bloco, numero_bloco, contratante FROM publicacoes WHERE arquivo_path = ? LIMIT 5', (pdf,))
            rows = db_cursor.fetchall()
            matched = None
            persisted_text = None
            persisted_ids = []
            for r in rows:
                pid, texto_bloco, numero_bloco, contratante = r
                persisted_ids.append({'id': pid, 'numero_bloco': numero_bloco, 'contratante': contratante})
                if numero_bloco == block_index:
                    persisted_text = texto_bloco
                    matched = (texto_bloco == entry.get('current_block_text'))
                    break
            entry['persisted_block_match'] = matched
            entry['persisted_textblock'] = persisted_text
            entry['persisted_rows_sample'] = persisted_ids
        except Exception as e:
            entry['persisted_lookup_error'] = str(e)

    results.append(entry)

# close DB
if db_conn:
    db_conn.close()

# write textual report
with open(TXT_OUT, 'w', encoding='utf-8') as f:
    f.write('Comparative report for split segmentation occurrences\n')
    f.write('='*80 + '\n\n')
    for r in results:
        f.write(f"Case {r['case_number']}: {r['pdf_path']}\n")
        f.write(f" Publication type: {r.get('publication_type')}\n")
        f.write(f" Block index: {r.get('block_index')} (prev: {r.get('previous_block_index')})\n")
        f.write(f" Contract previous: {r.get('contract_number_previous')} | Contract current: {r.get('contract_number_current')}\n")
        f.write(f" Process previous: {r.get('process_previous')} | Process current: {r.get('process_current')}\n")
        f.write(f" Prev has institutional Contratante?: {r.get('prev_has_institutional')}\n")
        f.write(f" Current has PELO CONTRATANTE?: {r.get('current_has_pelo_contratante')}\n")
        f.write(f" Persisted block match (same numero_bloco in DB): {r.get('persisted_block_match')}\n")
        f.write('\n-- Previous block tail (500 chars) --\n')
        f.write((r.get('prev_block_tail_500') or 'N/A') + '\n\n')
        f.write('-- Current block head (500 chars) --\n')
        f.write((r.get('current_block_head_500') or 'N/A') + '\n')
        f.write('\n' + ('-'*80) + '\n\n')

# write structured JSON
with open(JSON_OUT, 'w', encoding='utf-8') as f:
    json.dump({'generated_from_csv': CSV_IN, 'cases': results}, f, indent=2, ensure_ascii=False)

print('Wrote comparative TXT to', TXT_OUT)
print('Wrote comparative JSON to', JSON_OUT)
