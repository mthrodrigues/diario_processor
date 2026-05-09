from contextlib import contextmanager

from database import conectar


TIPOS_CONTRATUAIS_ANALITICOS = ("contrato", "extrato")


@contextmanager
def _conexao(conn=None):
    if conn is not None:
        yield conn
        return

    conn = conectar()

    try:
        yield conn
    finally:
        conn.close()


def _linhas_dict(cursor):
    colunas = [descricao[0] for descricao in cursor.description]
    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


def fornecedores_mais_recorrentes(limite=10, conn=None):
    with _conexao(conn) as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT
                fornecedor_normalizado,
                COUNT(*) AS ocorrencias,
                COALESCE(SUM(valor_principal), 0) AS valor_total,
                GROUP_CONCAT(DISTINCT contratante_normalizado) AS orgaos_relacionados,
                GROUP_CONCAT(DISTINCT fornecedor) AS fornecedores_originais
            FROM publicacoes
            WHERE fornecedor_normalizado IS NOT NULL
              AND TRIM(fornecedor_normalizado) <> ''
              AND tipo IN (?, ?)
            GROUP BY fornecedor_normalizado
            ORDER BY ocorrencias DESC, valor_total DESC, fornecedor_normalizado ASC
            LIMIT ?
            """,
            (*TIPOS_CONTRATUAIS_ANALITICOS, limite),
        )

        resultados = _linhas_dict(cursor)

    for resultado in resultados:
        resultado["orgaos_relacionados"] = _split_group_concat(resultado["orgaos_relacionados"])
        resultado["fornecedores_originais"] = _split_group_concat(resultado["fornecedores_originais"])

    return resultados


def orgaos_que_mais_contratam(limite=10, conn=None):
    with _conexao(conn) as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT
                contratante_normalizado,
                COUNT(*) AS quantidade_contratos,
                COALESCE(SUM(valor_principal), 0) AS valor_total
            FROM publicacoes
            WHERE contratante_normalizado IS NOT NULL
              AND TRIM(contratante_normalizado) <> ''
              AND tipo IN (?, ?)
            GROUP BY contratante_normalizado
            ORDER BY quantidade_contratos DESC, valor_total DESC, contratante_normalizado ASC
            LIMIT ?
            """,
            (*TIPOS_CONTRATUAIS_ANALITICOS, limite),
        )

        return _linhas_dict(cursor)


def maiores_contratos(limite=10, conn=None):
    with _conexao(conn) as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT
                contrato,
                fornecedor,
                contratante,
                valor_principal,
                objeto
            FROM publicacoes
            WHERE valor_principal IS NOT NULL
              AND tipo IN (?, ?)
            ORDER BY valor_principal DESC, contrato ASC
            LIMIT ?
            """,
            (*TIPOS_CONTRATUAIS_ANALITICOS, limite),
        )

        return _linhas_dict(cursor)


def contratos_por_periodo(ano=None, mes=None, data_inicio=None, data_fim=None, conn=None):
    filtros = ["tipo IN (?, ?)"]
    parametros = list(TIPOS_CONTRATUAIS_ANALITICOS)

    if ano is not None:
        filtros.append("CAST(strftime('%Y', data_processamento) AS INTEGER) = ?")
        parametros.append(ano)

    if mes is not None:
        filtros.append("CAST(strftime('%m', data_processamento) AS INTEGER) = ?")
        parametros.append(mes)

    if data_inicio is not None:
        filtros.append("date(data_processamento) >= date(?)")
        parametros.append(data_inicio)

    if data_fim is not None:
        filtros.append("date(data_processamento) <= date(?)")
        parametros.append(data_fim)

    where = " AND ".join(filtros)

    with _conexao(conn) as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            f"""
            SELECT
                strftime('%Y', data_processamento) AS ano,
                strftime('%m', data_processamento) AS mes,
                COUNT(*) AS quantidade_contratos,
                COALESCE(SUM(valor_principal), 0) AS valor_total
            FROM publicacoes
            WHERE {where}
            GROUP BY ano, mes
            ORDER BY ano DESC, mes DESC
            """,
            parametros,
        )

        return _linhas_dict(cursor)


def resumo_analitico(conn=None):
    return {
        "fornecedores_mais_recorrentes": fornecedores_mais_recorrentes(conn=conn),
        "orgaos_que_mais_contratam": orgaos_que_mais_contratam(conn=conn),
        "maiores_contratos": maiores_contratos(conn=conn),
        "contratos_por_periodo": contratos_por_periodo(conn=conn),
    }


def _split_group_concat(valor):
    if not valor:
        return []

    return [item for item in valor.split(",") if item]
