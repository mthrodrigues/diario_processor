from pathlib import Path

import pdfplumber

from extractor import extrair_texto
from parser import segmentar_publicacoes, identificar_tipo
from pot_extractor import extrair_publicacoes_pot_pdf
from scanner import extrair_diario_id

from infra.db.connection import postgres_connection
from infra.db.migrations.runner import run_migrations
from infra.db.repositories.publicacao_repository import (
    PublicacaoRepository,
)
from infra.db.repositories.pot_repository import (
    PotRepository,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_pot_postgres_real_fixtures():
    casos = [
        ("diario_3252.pdf", [104, 6, 6, 14]),
        ("diario_3352.pdf", [1]),
        ("diario_3431.pdf", [5]),
    ]

    with postgres_connection() as conn:
        run_migrations(
            conn,
            schema="diario",
        )

        publicacao_repository = PublicacaoRepository(
            conn,
            schema="diario",
        )

        pot_repository = PotRepository(
            conn,
            schema="diario",
        )

        for nome_pdf, tamanhos_esperados in casos:
            pdf_path = FIXTURES / nome_pdf
            diario_id = extrair_diario_id(pdf_path)

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

            assert len(blocos_pot) == len(
                publicacoes_pot
            ), nome_pdf

            assert [
                len(publicacao)
                for publicacao in publicacoes_pot
            ] == tamanhos_esperados, nome_pdf

            publicacao_ids = []

            for (
                (numero_bloco, bloco),
                registros,
            ) in zip(
                blocos_pot,
                publicacoes_pot,
            ):
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

                publicacao_ids.append(
                    publicacao_id
                )

                quantidade = (
                    pot_repository.substituir_registros(
                        publicacao_id,
                        registros,
                    )
                )

                assert quantidade == len(registros)

            # -------------------------------------------------
            # Primeira validação no banco
            # -------------------------------------------------

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.diario_id,
                        p.numero_bloco,
                        COUNT(pb.id) AS quantidade
                    FROM diario.publicacoes p
                    LEFT JOIN diario.pot_beneficiarios pb
                        ON pb.publicacao_id = p.id
                    WHERE p.id = ANY(%s)
                    GROUP BY
                        p.id,
                        p.diario_id,
                        p.numero_bloco
                    ORDER BY p.numero_bloco
                    """,
                    (publicacao_ids,),
                )

                resultados = cursor.fetchall()

            assert [
                linha[3]
                for linha in resultados
            ] == tamanhos_esperados, nome_pdf

            # -------------------------------------------------
            # Segunda gravação: valida idempotência
            # -------------------------------------------------

            for (
                publicacao_id,
                registros,
            ) in zip(
                publicacao_ids,
                publicacoes_pot,
            ):
                quantidade = (
                    pot_repository.substituir_registros(
                        publicacao_id,
                        registros,
                    )
                )

                assert quantidade == len(registros)

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.numero_bloco,
                        COUNT(pb.id) AS quantidade
                    FROM diario.publicacoes p
                    LEFT JOIN diario.pot_beneficiarios pb
                        ON pb.publicacao_id = p.id
                    WHERE p.id = ANY(%s)
                    GROUP BY p.numero_bloco
                    ORDER BY p.numero_bloco
                    """,
                    (publicacao_ids,),
                )

                resultados = cursor.fetchall()

            assert [
                linha[1]
                for linha in resultados
            ] == tamanhos_esperados, nome_pdf

        # -----------------------------------------------------
        # Não deixar absolutamente nada deste teste persistir.
        # -----------------------------------------------------
        conn.rollback()