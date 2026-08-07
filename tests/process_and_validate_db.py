import json
from extractor import extrair_texto
from parser import segmentar_publicacoes
from processor import extrair_metadados_bloco
from contextual_enrichment import aplicar_regra_001_heranca_contratante
from infra.db.connection import postgres_connection
from infra.db.repositories.publicacao_repository import PublicacaoRepository
from scanner import extrair_diario_id

PDF_PATH = r'C:\automacoes\diario_bot\pdfs\2026\06\diario_3375.pdf'


def fetch_publicacoes_map(conn, repo, arquivo_path):
    table = repo.table
    with conn.cursor() as cur:
        cur.execute(f"SELECT numero_bloco, texto_bloco, tipo, processo, contrato, contratante, fornecedor, cnpj, valores, valor_principal, vigencia, objeto FROM {table} WHERE arquivo_path = %s ORDER BY numero_bloco", (arquivo_path,))
        rows = cur.fetchall()
    result = {r[0]: {
        'texto_bloco': r[1], 'tipo': r[2], 'processo': r[3], 'contrato': r[4], 'contratante': r[5],
        'fornecedor': r[6], 'cnpj': r[7], 'valores': r[8], 'valor_principal': r[9], 'vigencia': r[10], 'objeto': r[11]
    } for r in rows}
    return result


def main():
    print('Starting DB validation for', PDF_PATH)
    with postgres_connection() as conn:
        repo = PublicacaoRepository(conn)
        # fetch before snapshot
        before = fetch_publicacoes_map(conn, repo, str(PDF_PATH))
        print('Before rows fetched:', sorted(before.keys()))

        # delete existing rows for a clean reprocess within this transaction
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {repo.table} WHERE arquivo_path = %s", (str(PDF_PATH),))
        print('Existing rows deleted within transaction (will be rolled back later).')

        # process PDF and insert
        texto = extrair_texto(PDF_PATH)
        blocos = segmentar_publicacoes(texto)
        diario_id = extrair_diario_id(PDF_PATH)

        previous_block = None
        previous_meta = None
        previous_num = None
        ec_applied_blocks = []

        for i, bloco in enumerate(blocos, start=1):
            metadados = extrair_metadados_bloco(bloco)
            updated_meta, applied, audit = aplicar_regra_001_heranca_contratante(
                previous_block, previous_meta, previous_num,
                bloco, metadados, i, str(PDF_PATH)
            )
            if applied:
                metadados = updated_meta
                ec_applied_blocks.append(i)
            # save publication
            repo.salvar_publicacao(
                diario_id,
                i,
                PDF_PATH,
                bloco,
                metadados['tipo'],
                metadados['processo'],
                metadados['contrato'],
                metadados['contratante'],
                metadados['fornecedor'],
                metadados['cnpj'],
                metadados['valores'],
                valor_principal=metadados.get('valor_principal'),
                vigencia=metadados.get('vigencia'),
                objeto=metadados.get('objeto'),
                fornecedor_normalizado=metadados.get('fornecedor_normalizado'),
                contratante_normalizado=metadados.get('contratante_normalizado'),
                processo_normalizado=metadados.get('processo_normalizado'),
                data_publicacao=None,
                contrato_normalizado=metadados.get('contrato_normalizado')
            )

            previous_block = bloco
            previous_meta = metadados
            previous_num = i

        # fetch after snapshot
        after = fetch_publicacoes_map(conn, repo, str(PDF_PATH))
        print('After rows fetched:', sorted(after.keys()))

        # compare
        changed_blocks = []
        other_field_changes = []
        for num, data_after in after.items():
            data_before = before.get(num)
            if not data_before:
                # new insertion where none existed before
                # treat as changed
                changed_blocks.append((num, None, data_after))
                continue
            # compare texto_bloco exact
            if data_before['texto_bloco'] != data_after['texto_bloco']:
                other_field_changes.append((num, 'texto_bloco', data_before['texto_bloco'], data_after['texto_bloco']))
            # collect differences in metadata
            for fld in ['tipo','processo','contrato','fornecedor','cnpj','valores','valor_principal','vigencia','objeto']:
                if data_before.get(fld) != data_after.get(fld):
                    other_field_changes.append((num, fld, data_before.get(fld), data_after.get(fld)))
            # contratante handled separately
            if data_before.get('contratante') != data_after.get('contratante'):
                changed_blocks.append((num, data_before.get('contratante'), data_after.get('contratante')))

        print('\nEC applied blocks during run:', ec_applied_blocks)
        print('\nBlocks with contratante change:')
        for cb in changed_blocks:
            print(cb)

        print('\nOther metadata/text changes detected (should be none):')
        for of in other_field_changes:
            print(of)

        # Rollback to leave DB unchanged
        conn.rollback()
        print('\nTransaction rolled back; no DB changes persisted.')

if __name__ == '__main__':
    main()
