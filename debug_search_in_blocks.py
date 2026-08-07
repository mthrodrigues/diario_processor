from extractor import extrair_texto
from parser import segmentar_publicacoes
import re
PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"
full_text = extrair_texto(PDF_PATH)
blocks = segmentar_publicacoes(full_text)

for idx in [3,4,2,8]:
    b = blocks[idx-1]
    print('\n--- Block', idx, 'length', len(b), '---')
    for m in re.finditer(r'(?i)contratante', b):
        s = m.start()
        e = m.end()
        start = max(0, s-80)
        end = min(len(b), e+80)
        print('found at', s, 'context:\n', b[start:end])
    for m in re.finditer(r'(?i)pelo\s+contratante', b):
        s = m.start()
        e = m.end()
        start = max(0, s-80)
        end = min(len(b), e+80)
        print('found PELO at', s, 'context:\n', b[start:end])
