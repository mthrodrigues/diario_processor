"""Consolidacao v1 de processos a partir das evidencias persistidas.

Quando varias publicacoes compartilham o mesmo processo_normalizado, o campo
processo recebe a menor representacao original nao vazia em ordem lexicografica.
Assim, o resultado nao depende da ordem de leitura das publicacoes.
"""

from datetime import datetime

from infra.db.migrations.runner import quote_ident


def consolidar_sqlite(conn):
    """Consolida publicacoes em processos usando uma conexao SQLite aberta."""
    _garantir_tabela_sqlite(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            processo_normalizado,
            MIN(NULLIF(TRIM(processo), '')),
            MIN(NULLIF(data_publicacao, '')),
            MAX(NULLIF(data_publicacao, '')),
            COUNT(*)
        FROM publicacoes
        WHERE processo_normalizado IS NOT NULL
          AND TRIM(processo_normalizado) <> ''
        GROUP BY processo_normalizado
        """
    )
    grupos = cursor.fetchall()
    agora = datetime.now().isoformat()

    for processo_normalizado, processo, primeira, ultima, quantidade in grupos:
        cursor.execute(
            "SELECT id, processo, data_primeira_publicacao, data_ultima_publicacao, "
            "quantidade_publicacoes, criado_em, atualizado_em "
            "FROM processos WHERE processo_normalizado = ?",
            (processo_normalizado,),
        )
        existente = cursor.fetchone()
        valores = (processo, primeira, ultima, quantidade)

        if existente is None:
            cursor.execute(
                """
                INSERT INTO processos (
                    processo, processo_normalizado, data_primeira_publicacao,
                    data_ultima_publicacao, quantidade_publicacoes, criado_em,
                    atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (processo, processo_normalizado, primeira, ultima, quantidade, agora, agora),
            )
        elif existente[1:5] != valores:
            cursor.execute(
                """
                UPDATE processos
                SET processo = ?, data_primeira_publicacao = ?,
                    data_ultima_publicacao = ?, quantidade_publicacoes = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                (*valores, agora, existente[0]),
            )

    conn.commit()
    return len(grupos)


def consolidar_postgres(conn, schema=None):
    """Consolida publicacoes em processos usando uma conexao PostgreSQL aberta."""
    schema = quote_ident(schema or "diario")
    publicacoes = f"{schema}.publicacoes"
    processos = f"{schema}.processos"

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                processo_normalizado,
                MIN(NULLIF(BTRIM(processo), '')),
                MIN(data_publicacao),
                MAX(data_publicacao),
                COUNT(*)
            FROM {publicacoes}
            WHERE processo_normalizado IS NOT NULL
              AND BTRIM(processo_normalizado) <> ''
            GROUP BY processo_normalizado
            """
        )
        grupos = cursor.fetchall()
        agora = datetime.now()

        for processo_normalizado, processo, primeira, ultima, quantidade in grupos:
            cursor.execute(
                f"""
                INSERT INTO {processos} (
                    processo, processo_normalizado, data_primeira_publicacao,
                    data_ultima_publicacao, quantidade_publicacoes, criado_em,
                    atualizado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (processo_normalizado) DO UPDATE SET
                    processo = EXCLUDED.processo,
                    data_primeira_publicacao = EXCLUDED.data_primeira_publicacao,
                    data_ultima_publicacao = EXCLUDED.data_ultima_publicacao,
                    quantidade_publicacoes = EXCLUDED.quantidade_publicacoes,
                    atualizado_em = EXCLUDED.atualizado_em
                WHERE {processos}.processo IS DISTINCT FROM EXCLUDED.processo
                   OR {processos}.data_primeira_publicacao IS DISTINCT FROM
                      EXCLUDED.data_primeira_publicacao
                   OR {processos}.data_ultima_publicacao IS DISTINCT FROM
                      EXCLUDED.data_ultima_publicacao
                   OR {processos}.quantidade_publicacoes IS DISTINCT FROM
                      EXCLUDED.quantidade_publicacoes
                """,
                (processo, processo_normalizado, primeira, ultima, quantidade, agora, agora),
            )

    return len(grupos)


def _garantir_tabela_sqlite(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT NOT NULL,
            processo_normalizado TEXT NOT NULL UNIQUE,
            data_primeira_publicacao TEXT,
            data_ultima_publicacao TEXT,
            quantidade_publicacoes INTEGER NOT NULL,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
        """
    )
