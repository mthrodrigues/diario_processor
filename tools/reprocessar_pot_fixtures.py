import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pdfplumber

from extractor import extrair_texto
from parser import identificar_tipo, segmentar_publicacoes
from pot_extractor import extrair_publicacoes_pot_pdf
from scanner import extrair_diario_id

from config import get_postgres_config
from infra.db.connection import postgres_connection
from infra.db.migrations.runner import run_migrations
from infra.db.repositories.publicacao_repository import (
    PublicacaoRepository,
)
from infra.db.repositories.pot_repository import (
    PotRepository,
)


SCHEMA = get_postgres_config().schema

PDFS = (
    Path(r"C:\automacoes\diario_bot\pdfs\2026\01\diario_3216.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\02\diario_3246.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\03\diario_3279.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\03\diario_3295.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3330.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3344.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3350.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3354.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3367.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\07\diario_3396.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\08\diario_3418.pdf"),
    Path(r"C:\automacoes\diario_bot\pdfs\2026\08\diario_3430.pdf"),
)


def localizar_publicacao_pot(
    conn,
    diario_id,
    numero_bloco,
    arquivo_path,
):
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id
            FROM "{SCHEMA}".publicacoes
            WHERE diario_id = %s
              AND numero_bloco = %s
              AND tipo = 'pot'
              AND arquivo_path = %s
            ORDER BY id
            LIMIT 1
            """,
            (
                diario_id,
                numero_bloco,
                str(arquivo_path),
            ),
        )

        linha = cursor.fetchone()

    return linha[0] if linha else None


def main():
    with postgres_connection() as conn:
        run_migrations(
            conn,
            schema=SCHEMA,
        )

        publicacao_repository = PublicacaoRepository(
            conn,
            schema=SCHEMA,
        )

        pot_repository = PotRepository(
            conn,
            schema=SCHEMA,
        )

        for pdf_path in PDFS:
            diario_id = extrair_diario_id(pdf_path)

            print()
            print("=" * 72)
            print(f"DIÁRIO {diario_id} | {pdf_path.name}")
            print("=" * 72)

            texto = extrair_texto(str(pdf_path))
            blocos = segmentar_publicacoes(texto)

            blocos_pot = [
                (numero_bloco, bloco)
                for numero_bloco, bloco in enumerate(
                    blocos,
                    start=1,
                )
                if identificar_tipo(bloco) == "pot"
            ]

            with pdfplumber.open(pdf_path) as pdf:
                publicacoes_pot = (
                    extrair_publicacoes_pot_pdf(pdf)
                )

            print(
                f"Blocos POT: {len(blocos_pot)}"
            )
            print(
                f"Publicações POT extraídas: "
                f"{len(publicacoes_pot)}"
            )

            if len(blocos_pot) != len(publicacoes_pot):
                raise RuntimeError(
                    "Divergência POT: "
                    f"{len(blocos_pot)} blocos vs "
                    f"{len(publicacoes_pot)} grupos."
                )

            for (
                (numero_bloco, bloco),
                registros,
            ) in zip(
                blocos_pot,
                publicacoes_pot,
            ):
                publicacao_id = localizar_publicacao_pot(
                    conn,
                    diario_id,
                    numero_bloco,
                    pdf_path,
                )

                if publicacao_id is None:
                    publicacao_id = (
                        publicacao_repository.salvar_publicacao(
                            diario_id=diario_id,
                            numero_bloco=numero_bloco,
                            arquivo_path=str(pdf_path),
                            texto_bloco=bloco,
                            tipo="pot",
                            processo=None,
                            contrato=None,
                            contratante=None,
                            fornecedor=None,
                            cnpj=None,
                            valores=[],
                            valor_principal=None,
                            vigencia=None,
                            objeto=None,
                            fornecedor_normalizado=None,
                            contratante_normalizado=None,
                            processo_normalizado=None,
                            data_publicacao=None,
                            contrato_normalizado=None,
                        )
                    )

                    acao = "CRIADA"
                else:
                    acao = "REUTILIZADA"

                quantidade = (
                    pot_repository.substituir_registros(
                        publicacao_id,
                        registros,
                    )
                )

                print(
                    f"bloco {numero_bloco:>2} | "
                    f"publicacao_id={publicacao_id:>6} | "
                    f"{acao:<9} | "
                    f"{quantidade:>3} registros"
                )

            conn.commit()

            print("COMMIT OK")


if __name__ == "__main__":
    main()