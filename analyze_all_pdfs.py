from scanner import listar_pdfs
from extractor import extrair_texto
from parser import segmentar_publicacoes, extrair_contrato, extrair_processo, identificar_tipo
from database import conectar as db_conectar
import re
import csv
import json
import os

pdfs = listar_pdfs()
print('Found', len(pdfs), 'pdfs under BASE_DIARIO_PATH')

# process all PDFs (full corpus run)
LIMIT = None

# outputs
CSV_PATH = os.path.join(os.getcwd(), 'split_segmentation_report.csv')
JSON_PATH = os.path.join(os.getcwd(), 'split_segmentation_summary.json')

cases = []
summary_by_type = {}
total_blocks = 0
contract_like_types = set(['contrato', 'aditivo', 'apostilamento', 'extrato'])
contract_like_counts = {t: 0 for t in contract_like_types}

# prepare DB connection for persisted_block matching (best-effort)
db_conn = None
try:
    db_conn = db_conectar()
    db_cursor = db_conn.cursor()
    print('Opened local DB connection for persisted block matching')
except Exception as e:
    print('Could not open local DB, persisted_block_match will be set to null:', e)
    db_conn = None

for idx, pdf in enumerate(pdfs):
    if LIMIT and idx >= LIMIT:
        break
    pdf = str(pdf)
    print(f'[{idx+1}/{len(pdfs)}] Processing', pdf)
    try:
        text = extrair_texto(pdf)
    except Exception as e:
        print(' Error extracting', pdf, e)
        continue

    try:
        blocks = segmentar_publicacoes(text)
    except Exception as e:
        print(' Error segmenting', pdf, e)
        continue

    total_blocks += len(blocks)

    # count totals per type
    for block in blocks:
        t = identificar_tipo(block)
        summary_by_type.setdefault(t, {'cases': 0, 'total': 0})
        summary_by_type[t]['total'] += 1
        if t in contract_like_types:
            contract_like_counts[t] = contract_like_counts.get(t, 0) + 1

    # collect detailed cases
    for i, block in enumerate(blocks):
        has_pelo = re.search(r'\bpelo\s+contratante\b', block, flags=re.IGNORECASE) is not None
        has_institutional = re.search(r'(?i)(?<!pelo )(?<!pela )\bcontratante\s*:', block) is not None
        if has_pelo and not has_institutional:
            prev = blocks[i-1] if i-1 >= 0 else None
            c_this = extrair_contrato(block)
            p_this = extrair_processo(block)
            c_prev = extrair_contrato(prev) if prev else None
            p_prev = extrair_processo(prev) if prev else None

            doc_type = identificar_tipo(block)
            summary_by_type.setdefault(doc_type, {'cases': 0, 'total': 0})
            summary_by_type[doc_type]['cases'] += 1

            # persisted block match: best-effort lookup in local sqlite publicacoes
            persisted_match = None
            try:
                if db_conn:
                    db_cursor.execute(
                        "SELECT texto_bloco FROM publicacoes WHERE arquivo_path = ? AND numero_bloco = ? LIMIT 1",
                        (pdf, i+1)
                    )
                    row = db_cursor.fetchone()
                    if row:
                        texto_persistido = row[0]
                        persisted_match = (texto_persistido == block)
                    else:
                        persisted_match = False
            except Exception:
                persisted_match = None

            cases.append({
                'pdf_path': pdf,
                'publication_type': doc_type,
                'block_index': i+1,
                'previous_block_index': i if i>=1 else None,
                'contract_number_previous': c_prev,
                'contract_number_current': c_this,
                'process_previous': p_prev,
                'process_current': p_this,
                'has_institutional_contratante_previous': bool(prev and re.search(r'(?i)(?<!pelo )(?<!pela )\\bcontratante\s*:', prev)),
                'has_institutional_contratante_current': bool(has_institutional),
                'has_pelo_contratante_current': bool(has_pelo),
                'persisted_block_match': persisted_match,
                'this_head': block[:300],
                'this_tail': block[-300:],
                'prev_tail': prev[-300:] if prev else None,
            })

# finalize DB connection
if db_conn:
    db_conn.close()

# write CSV
fieldnames = [
    'pdf_path',
    'publication_type',
    'block_index',
    'previous_block_index',
    'contract_number_previous',
    'contract_number_current',
    'process_previous',
    'process_current',
    'has_institutional_contratante_previous',
    'has_institutional_contratante_current',
    'has_pelo_contratante_current',
    'persisted_block_match',
]

with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in cases:
        out = {k: row.get(k) for k in fieldnames}
        writer.writerow(out)

# build JSON summary
total_pdfs = len(pdfs)

total_occurrences = len(cases)

total_contract_like_blocks = sum(contract_like_counts.values())

occurrences_by_document_type = {t: summary_by_type.get(t, {}).get('cases', 0) for t in summary_by_type}
percentage_by_document_type = {}
for t, vals in summary_by_type.items():
    total = vals.get('total', 0)
    cases_count = vals.get('cases', 0)
    pct = (cases_count / total * 100) if total > 0 else 0
    percentage_by_document_type[t] = pct

summary = {
    'total_pdfs': total_pdfs,
    'total_blocks': total_blocks,
    'total_contract_like_blocks': total_contract_like_blocks,
    'total_occurrences': total_occurrences,
    'occurrences_by_document_type': occurrences_by_document_type,
    'percentage_by_document_type': percentage_by_document_type,
}

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print('\nFinished full-corpus analysis')
print('CSV written to', CSV_PATH)
print('JSON summary written to', JSON_PATH)
