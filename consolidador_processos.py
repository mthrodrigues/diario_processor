"""Consolidacao v1 de processos a partir das evidencias persistidas.

Quando varias publicacoes compartilham o mesmo processo_normalizado, o campo
processo recebe a menor representacao original nao vazia em ordem lexicografica.
Assim, o resultado nao depende da ordem de leitura das publicacoes.
"""

from datetime import datetime

from consolidacao import executar
from infra.db.migrations.runner import quote_ident
from normalizer import normalize_processo


def obter_ou_criar_processo(conn, processo, schema=None):
    """Retorna o ID do processo, criando o catálogo quando necessário."""
    processo_normalizado = normalize_processo(processo)

    if processo_normalizado is None:
        return None

    schema = quote_ident(schema or "diario")
    tabela = f"{schema}.processos"

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {tabela} (
                processo,
                processo_normalizado,
                quantidade_publicacoes
            ) VALUES (%s, %s, 0)
            ON CONFLICT (processo_normalizado) DO NOTHING
            """,
            (
                processo,
                processo_normalizado,
            ),
        )

        cursor.execute(
            f"""
            SELECT id
            FROM {tabela}
            WHERE processo_normalizado = %s
            """,
            (processo_normalizado,),
        )

        resultado = cursor.fetchone()

    return resultado[0] if resultado else None


def consolidar_sqlite(conn):
    """Consolida publicacoes em processos usando uma conexao SQLite aberta."""

    def carregar_grupos(conexao):
        cursor = conexao.cursor()
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
        return cursor.fetchall()

    agora = datetime.now().isoformat()

    def persistir_grupo(conexao, grupo):
        processo_normalizado, processo, primeira, ultima, quantidade = grupo
        cursor = conexao.cursor()
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
                (
                    processo,
                    processo_normalizado,
                    primeira,
                    ultima,
                    quantidade,
                    agora,
                    agora,
                ),
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

    quantidade_grupos = executar(
        conn,
        carregar_grupos,
        persistir_grupo,
        preparar=_garantir_tabela_sqlite,
    )
    conn.commit()
    return quantidade_grupos


def consolidar_postgres(conn, schema=None):
    """Consolida publicacoes em processos usando uma conexao PostgreSQL aberta."""
    schema = quote_ident(schema or "diario")
    publicacoes = f"{schema}.publicacoes"
    processos = f"{schema}.processos"
    publicacao_processos = f"{schema}.publicacao_processos"

    def carregar_grupos(conexao):
        with conexao.cursor() as cursor:
            cursor.execute(
                f"""
                WITH fontes AS (
                    SELECT
                        processo_normalizado,
                        NULLIF(BTRIM(processo), '') AS processo,
                        data_publicacao,
                        id AS publicacao_id
                    FROM {publicacoes}
                    WHERE processo_normalizado IS NOT NULL
                      AND BTRIM(processo_normalizado) <> ''

                    UNION ALL

                    SELECT
                        p.processo_normalizado,
                        NULLIF(BTRIM(p.processo), '') AS processo,
                        pub.data_publicacao,
                        pp.publicacao_id
                    FROM {publicacao_processos} pp
                    JOIN {processos} p
                        ON p.id = pp.processo_id
                    JOIN {publicacoes} pub
                        ON pub.id = pp.publicacao_id
                    WHERE p.processo_normalizado IS NOT NULL
                      AND BTRIM(p.processo_normalizado) <> ''
                )
                SELECT
                    processo_normalizado,
                    MIN(processo),
                    MIN(data_publicacao),
                    MAX(data_publicacao),
                    COUNT(DISTINCT publicacao_id)
                FROM fontes
                GROUP BY processo_normalizado
                """
            )
            return cursor.fetchall()

    agora = datetime.now()

    def persistir_grupo(conexao, grupo):
        processo_normalizado, processo, primeira, ultima, quantidade = grupo
        with conexao.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {processos} (
                    processo,
                    processo_normalizado,
                    data_primeira_publicacao,
                    data_ultima_publicacao,
                    quantidade_publicacoes,
                    criado_em,
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
                (
                    processo,
                    processo_normalizado,
                    primeira,
                    ultima,
                    quantidade,
                    agora,
                    agora,
                ),
            )

    return executar(conn, carregar_grupos, persistir_grupo)


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
