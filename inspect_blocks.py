from extractor import extrair_texto
from parser import segmentar_publicacoes

PDF_PATH = r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf"
full_text = extrair_texto(PDF_PATH)
blocks = segmentar_publicacoes(full_text)

for i, b in enumerate(blocks[:8], start=1):
    print('\n===== BLOCK', i, 'START =====')
    print(b)
    print('===== BLOCK', i, 'END =====\n')
    
print('\n--- search summaries ---\n')
for i, b in enumerate(blocks[:8], start=1):
    lower = b.lower()
    print(f'Block {i}: contains "contratante:"? {"contratante:" in lower}, contains "pelo contratante"? {"pelo contratante" in lower}')
