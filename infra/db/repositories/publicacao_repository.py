import json
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from config import get_postgres_config
from infra.db.migrations.runner import quote_ident
from normalizer import normalize_contratante


class PublicacaoRepository:
    def __init__(self, conn, schema=None):
        self.conn = conn
        self.schema = quote_ident(schema or get_postgres_config().schema)
        self.table = f"{self.schema}.publicacoes"

    def _emitir_audit(self, prefix, extra=None):
        pass  # instrumentação de investigação desativada

    def salvar_publicacao(
        self,
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
        contratante_normalizado_canonico = normalize_contratante(contratante)
        if contratante_normalizado != contratante_normalizado_canonico:
            contratante_normalizado = contratante_normalizado_canonico

        with self.conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {self.table} (
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
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s
                )
                """
            params = (
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
                json.dumps(valores or []),
                valor_principal,
                vigencia,
                objeto,
                datetime.now(),
                processo_normalizado,
                data_publicacao,
            )
            cursor.execute(sql, params)

    def ja_processado(self, arquivo_path):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 1
                FROM {self.table}
                WHERE arquivo_path = %s
                LIMIT 1
                """,
                (str(arquivo_path),),
            )
            return cursor.fetchone() is not None

    def listar_fornecedores_consolidados(self):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    fornecedor_normalizado,
                    COUNT(*) AS ocorrencias,
                    COALESCE(SUM(valor_principal), 0) AS valor_total,
                    ARRAY_REMOVE(ARRAY_AGG(DISTINCT fornecedor), NULL) AS fornecedores_originais
                FROM {self.table}
                WHERE fornecedor_normalizado IS NOT NULL
                  AND TRIM(fornecedor_normalizado) <> ''
                GROUP BY fornecedor_normalizado
                ORDER BY ocorrencias DESC, valor_total DESC, fornecedor_normalizado ASC
                """
            )

            return [
                {
                    "fornecedor_normalizado": linha[0],
                    "ocorrencias": linha[1],
                    "valor_total": linha[2],
                    "fornecedores_originais": linha[3] or [],
                }
                for linha in cursor.fetchall()
            ]
