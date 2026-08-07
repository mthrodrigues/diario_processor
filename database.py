import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH


# 🔌 Conexão
def conectar():
    return sqlite3.connect(DATABASE_PATH)


# 🗄️ Criação de tabela
def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publicacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diario_id INTEGER,
        numero_bloco INTEGER,
        arquivo_path TEXT,
        texto_bloco TEXT,
        tipo TEXT,
        processo TEXT,
        contrato TEXT,
        contrato_normalizado TEXT,
        contratante TEXT,
        fornecedor TEXT,
        fornecedor_normalizado TEXT,
        contratante_normalizado TEXT,
        cnpj TEXT,
        valores TEXT,
        valor_principal REAL,
        vigencia TEXT,
        objeto TEXT,
        data_processamento TEXT,
        processo_normalizado TEXT,
        data_publicacao TEXT
    )
    """)

    cursor.execute("""
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
    """)

    cursor.execute("""
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
    """)

    garantir_colunas_publicacoes(cursor)

    conn.commit()
    conn.close()


def garantir_colunas_publicacoes(cursor):
    cursor.execute("PRAGMA table_info(publicacoes)")
    colunas = {coluna[1] for coluna in cursor.fetchall()}

    colunas_esperadas = {
        "id",
        "diario_id",
        "numero_bloco",
        "arquivo_path",
        "texto_bloco",
        "tipo",
        "processo",
        "contrato",
        "contrato_normalizado",
        "contratante",
        "fornecedor",
        "fornecedor_normalizado",
        "contratante_normalizado",
        "cnpj",
        "valores",
        "valor_principal",
        "vigencia",
        "objeto",
        "data_processamento",
        "processo_normalizado",
        "data_publicacao",
    }

    for coluna in sorted(colunas - colunas_esperadas):
        cursor.execute("PRAGMA index_list(publicacoes)")
        for indice in cursor.fetchall():
            nome_indice = indice[1]
            cursor.execute(f'PRAGMA index_info("{nome_indice}")')
            colunas_indice = {linha[2] for linha in cursor.fetchall()}
            if coluna in colunas_indice:
                cursor.execute(f'DROP INDEX IF EXISTS "{nome_indice}"')

        cursor.execute(f'ALTER TABLE publicacoes DROP COLUMN "{coluna}"')

    colunas_novas = {
        "valor_principal": "REAL",
        "vigencia": "TEXT",
        "objeto": "TEXT",
        "fornecedor_normalizado": "TEXT",
        "contratante_normalizado": "TEXT",
        "processo_normalizado": "TEXT",
        "contrato_normalizado": "TEXT",
        "data_publicacao": "TEXT",
    }

    for nome, tipo in colunas_novas.items():
        if nome not in colunas:
            cursor.execute(f"ALTER TABLE publicacoes ADD COLUMN {nome} {tipo}")

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_fornecedor_normalizado
    ON publicacoes (fornecedor_normalizado)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_contratante_normalizado
    ON publicacoes (contratante_normalizado)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_processo_normalizado
    ON publicacoes (processo_normalizado)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_contrato_normalizado
    ON publicacoes (contrato_normalizado)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_valor_principal
    ON publicacoes (valor_principal)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_tipo
    ON publicacoes (tipo)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_publicacoes_data_processamento
    ON publicacoes (data_processamento)
    """)


# 💾 Salva uma publicação/bloco
def salvar_publicacao(
    diario_id,
    numero_bloco,
    arquivo_path,
    texto_bloco,
    tipo,
    processo,
    contrato,
    contratante,
    fornecedor,
    cnpj,
    valores,
    valor_principal=None,
    vigencia=None,
    objeto=None,
    fornecedor_normalizado=None,
    contratante_normalizado=None,
    processo_normalizado=None,
    data_publicacao=None,
    contrato_normalizado=None,
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO publicacoes (
        diario_id,
        numero_bloco,
        arquivo_path,
        texto_bloco,
        tipo,
        processo,
        contrato,
        contrato_normalizado,
        contratante,
        fornecedor,
        fornecedor_normalizado,
        contratante_normalizado,
        cnpj,
        valores,
        valor_principal,
        vigencia,
        objeto,
        data_processamento,
        processo_normalizado,
        data_publicacao
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        diario_id,
        numero_bloco,
        str(arquivo_path),
        texto_bloco,
        tipo,
        processo,
        contrato,
        contrato_normalizado,
        contratante,
        fornecedor,
        fornecedor_normalizado,
        contratante_normalizado,
        cnpj,
        json.dumps(valores),
        valor_principal,
        vigencia,
        objeto,
        datetime.now().isoformat(),
        processo_normalizado,
        data_publicacao,
    ))

    conn.commit()
    conn.close()


def listar_fornecedores_consolidados():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        fornecedor_normalizado,
        COUNT(*) AS ocorrencias,
        COALESCE(SUM(valor_principal), 0) AS valor_total,
        GROUP_CONCAT(DISTINCT fornecedor) AS fornecedores_originais
    FROM publicacoes
    WHERE fornecedor_normalizado IS NOT NULL
      AND TRIM(fornecedor_normalizado) <> ''
    GROUP BY fornecedor_normalizado
    ORDER BY ocorrencias DESC, valor_total DESC, fornecedor_normalizado ASC
    """)

    resultados = []

    for fornecedor_normalizado, ocorrencias, valor_total, fornecedores_originais in cursor.fetchall():
        variantes = fornecedores_originais.split(",") if fornecedores_originais else []
        resultados.append(
            {
                "fornecedor_normalizado": fornecedor_normalizado,
                "ocorrencias": ocorrencias,
                "valor_total": valor_total,
                "fornecedores_originais": variantes,
            }
        )

    conn.close()

    return resultados


# 🔍 Verifica se diário já foi processado
def ja_processado(arquivo_path):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 1
    FROM publicacoes
    WHERE arquivo_path = ?
    LIMIT 1
    """, (str(arquivo_path),))

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None
