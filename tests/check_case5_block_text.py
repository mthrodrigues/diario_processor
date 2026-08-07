import os
import json

PDF_PATH = r'C:\automacoes\diario_bot\pdfs\2026\08\diario_3417.pdf'
from extractor import extrair_texto
from parser import segmentar_publicacoes


def find_contract_in_block(pdf_path, target_contract, block_index):
    texto = extrair_texto(pdf_path)
    blocks = segmentar_publicacoes(texto)
    # block_index is 1-based
    if block_index < 1 or block_index > len(blocks):
        print(json.dumps({'error': 'block_index_out_of_range', 'blocks_count': len(blocks)}))
        return
    bloco = blocks[block_index - 1]
    # search for exact substring
    idx = bloco.find(target_contract)
    if idx == -1:
        print(json.dumps({'found': False, 'block_index': block_index, 'contract': target_contract}))
    else:
        # give approximate position and snippet
        start = max(0, idx - 60)
        end = min(len(bloco), idx + len(target_contract) + 60)
        snippet = bloco[start:end]
        print(json.dumps({'found': True, 'block_index': block_index, 'contract': target_contract, 'index': idx, 'snippet': snippet}))


if __name__ == '__main__':
    find_contract_in_block(PDF_PATH, '002.031.2026', 4)
