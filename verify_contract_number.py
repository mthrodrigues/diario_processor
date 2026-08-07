from extractor import extrair_texto
from parser import segmentar_publicacoes
PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"
full_text = extrair_texto(PDF_PATH)
blocks = segmentar_publicacoes(full_text)
prev = blocks[2]
curr = blocks[3]
search = '008.009.2025'
print('in prev?:', search in prev)
print('prev index:', prev.find(search))
print('\nprev context around search:\n', prev[prev.find(search)-40:prev.find(search)+40])
print('\nin curr?:', search in curr)
print('curr index:', curr.find(search))
print('\ncurr context around search:\n', curr[curr.find(search)-40:curr.find(search)+40])
