"""Consolidacao v1 de contratos a partir das evidencias persistidas.

Quando varias publicacoes compartilham o mesmo contrato_normalizado, o campo
contrato recebe a menor representacao original nao vazia em ordem lexicografica.
"""

from datetime import datetime

from consolidacao import executar
from infra.db.migrations.runner import quote_ident


def consolidar_sqlite(conn):
    """Consolida publicacoes em contratos usando uma conexao SQLite aberta."""
    def carregar_grupos(conexao):
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT
                contrato_normalizado,
                MIN(NULLIF(TRIM(contrato), '')),
                MIN(NULLIF(data_publicacao, '')),
                MAX(NULLIF(data_publicacao, '')),
                COUNT(*)
            FROM publicacoes
            WHERE contrato_normalizado IS NOT NULL
              AND TRIM(contrato_normalizado) <> ''
            GROUP BY contrato_normalizado
            """
        )
        return cursor.fetchall()

    agora = datetime.now().isoformat()

    def persistir_grupo(conexao, grupo):
        contrato_normalizado, contrato, primeira, ultima, quantidade = grupo
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id, contrato, data_primeira_publicacao, data_ultima_publicacao, "
            "quantidade_publicacoes, criado_em, atualizado_em "
            "FROM contratos WHERE contrato_normalizado = ?",
            (contrato_normalizado,),
        )
        existente = cursor.fetchone()
        valores = (contrato, primeira, ultima, quantidade)

        if existente is None:
            cursor.execute(
                """
                INSERT INTO contratos (
                    contrato, contrato_normalizado, data_primeira_publicacao,
                    data_ultima_publicacao, quantidade_publicacoes, criado_em,
                    atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (contrato, contrato_normalizado, primeira, ultima, quantidade, agora, agora),
            )
        elif existente[1:5] != valores:
            cursor.execute(
                """
                UPDATE contratos
                SET contrato = ?, data_primeira_publicacao = ?,
                    data_ultima_publicacao = ?, quantidade_publicacoes = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                (*valores, agora, existente[0]),
            )

    quantidade_grupos = executar(
        conn,
        carregar_grupos,
        persistir_grupo,
        preparar=_garantir_tabela_sqlite,
    )
    conn.commit()
    return quantidade_grupos


def consolidar_postgres(conn, schema=None):
    """Consolida publicacoes em contratos usando uma conexao PostgreSQL aberta."""
    schema = quote_ident(schema or "diario")
    publicacoes = f"{schema}.publicacoes"
    contratos = f"{schema}.contratos"

    def carregar_grupos(conexao):
        with conexao.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    contrato_normalizado,
                    MIN(NULLIF(BTRIM(contrato), '')),
                    MIN(data_publicacao),
                    MAX(data_publicacao),
                    COUNT(*)
                FROM {publicacoes}
                WHERE contrato_normalizado IS NOT NULL
                  AND BTRIM(contrato_normalizado) <> ''
                GROUP BY contrato_normalizado
                """
            )
            return cursor.fetchall()

    agora = datetime.now()

    def persistir_grupo(conexao, grupo):
        contrato_normalizado, contrato, primeira, ultima, quantidade = grupo
        with conexao.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {contratos} (
                    contrato, contrato_normalizado, data_primeira_publicacao,
                    data_ultima_publicacao, quantidade_publicacoes, criado_em,
                    atualizado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (contrato_normalizado) DO UPDATE SET
                    contrato = EXCLUDED.contrato,
                    data_primeira_publicacao = EXCLUDED.data_primeira_publicacao,
                    data_ultima_publicacao = EXCLUDED.data_ultima_publicacao,
                    quantidade_publicacoes = EXCLUDED.quantidade_publicacoes,
                    atualizado_em = EXCLUDED.atualizado_em
                WHERE {contratos}.contrato IS DISTINCT FROM EXCLUDED.contrato
                   OR {contratos}.data_primeira_publicacao IS DISTINCT FROM
                      EXCLUDED.data_primeira_publicacao
                   OR {contratos}.data_ultima_publicacao IS DISTINCT FROM
                      EXCLUDED.data_ultima_publicacao
                   OR {contratos}.quantidade_publicacoes IS DISTINCT FROM
                      EXCLUDED.quantidade_publicacoes
                """,
                (contrato, contrato_normalizado, primeira, ultima, quantidade, agora, agora),
            )

    return executar(conn, carregar_grupos, persistir_grupo)


def _garantir_tabela_sqlite(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato TEXT NOT NULL,
            contrato_normalizado TEXT NOT NULL UNIQUE,
            data_primeira_publicacao TEXT,
            data_ultima_publicacao TEXT,
            quantidade_publicacoes INTEGER NOT NULL,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
        """
    )
