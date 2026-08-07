import pdfplumber
from ftfy import fix_text
from extractor import extrair_texto
from parser import segmentar_publicacoes

PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"

# The persisted texto_bloco as provided earlier
persisted_texto_bloco = '''termo aditivo ao Contrato n.º 008.009.2025, a prorrogação de prazo por mais 12 (doze)
meses a partir da data de vencimento em (25/06/2026), com fundamento no art. 107 da
Lei 14.133/21.. Valor R$: 629.332,62 (seiscentos e vinte e nove mil, trezentos e trinta e
dois reais e sessenta e dois centavos). Processo n° 1.438/2025.
PELO CONTRATANTE: CARLA RABELLO FERREIRA.
PELA CONTRATADA: RENATA NUNES FERREIRA.
'''

print('1) PDF inspection: locating occurrences per page')
with pdfplumber.open(PDF_PATH) as pdf:
    page_texts = []
    for i, page in enumerate(pdf.pages, start=1):
        txt = page.extract_text() or ''
        txt = fix_text(txt)
        page_texts.append(txt)
        lower = txt.lower()
        if 'contratante' in lower or 'pelo contratante' in lower:
            print(f'-- Page {i} (length {len(txt)} chars) --')
            # show small context around occurrences
            for key in ['contratante', 'pelo contratante']:
                idx = lower.find(key)
                if idx != -1:
                    start = max(0, idx-80)
                    end = min(len(txt), idx+80)
                    print(f"Found '{key}' at pos {idx} in page {i}")
                    print('Context:')
                    print(txt[start:end])
                    print('-----')

print('\n2) extractor.extrair_texto (combined text) — getting full text and size')
full_text = extrair_texto(PDF_PATH)
print('Combined text length:', len(full_text))

# Look for occurrences in combined text
lower_full = full_text.lower()
for key in ['contratante', 'pelo contratante']:
    idx = lower_full.find(key)
    print(f"Index of '{key}' in combined text: {idx}")
    if idx != -1:
        start = max(0, idx-120)
        end = min(len(full_text), idx+120)
        print(full_text[start:end])
        print('-----')

print('\n3) Confirm after fix_text already applied by extractor (extractor used fix_text)')
# We already used extractor which applies fix_text; the full_text printed above is after fix_text

print('\n4) segmentar_publicacoes() — produce blocks and their indices in combined text')
blocks = segmentar_publicacoes(full_text)
print('Number of blocks produced:', len(blocks))

# Compute indices by searching for each block sequentially
indices = []
search_pos = 0
for i, block in enumerate(blocks, start=1):
    # find block starting from search_pos
    pos = full_text.find(block, search_pos)
    if pos == -1:
        # fallback: try global find
        pos = full_text.find(block)
    endpos = pos + len(block) if pos != -1 else -1
    indices.append((i, pos, endpos))
    search_pos = endpos if endpos != -1 else search_pos

for i, pos, endpos in indices:
    print(f'\n--- Block {i} ---')
    print('Start index in combined text:', pos)
    print('End index:', endpos)
    preview_first = blocks[i-1][:300].replace('\n','\n')
    preview_last = blocks[i-1][-300:].replace('\n','\n')
    print('\nFirst 300 chars:\n')
    print(preview_first)
    print('\nLast 300 chars:\n')
    print(preview_last)
    # check for presence of labels
    b_lower = blocks[i-1].lower()
    if 'contratante' in b_lower:
        if 'pelo contratante' in b_lower:
            print('\nBlock contains: PELO CONTRATANTE')
        else:
            print('\nBlock contains: Contratante:')

# Identify which block matches the persisted texto_bloco exactly
matched_block_index = None
for i, block in enumerate(blocks, start=1):
    # normalize newlines for comparison
    if block.strip() == persisted_texto_bloco.strip():
        matched_block_index = i
        break

print('\n5) Comparison with persisted texto_bloco (provided)')
print('Found exact match in segmentation blocks?' , matched_block_index is not None)
if matched_block_index:
    print('Persisted texto_bloco corresponds to Block', matched_block_index)
    print('Block content preview (first 500 chars):\n')
    print(blocks[matched_block_index-1][:500])
else:
    # show blocks that contain the signature
    print('No exact block match. Blocks containing "PELO CONTRATANTE" (if any):')
    for i, block in enumerate(blocks, start=1):
        if 'pelo contratante' in block.lower():
            print('Block', i, 'contains PELO CONTRATANTE')

print('\n6) End of pipeline trace script')
