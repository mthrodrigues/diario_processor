import json
import os
import subprocess
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
        cfg = get_postgres_config()
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
            branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, text=True).strip()
        except Exception as exc:
            commit_sha = f"ERR:{exc}"
            branch_name = f"ERR:{exc}"

        payload = {
            "commit_sha": commit_sha,
            "branch": branch_name,
            "pid": os.getpid(),
            "db": cfg.db,
            "host": cfg.host,
            "schema": cfg.schema,
        }
        if extra:
            payload.update(extra)
        print(f"[AUDIT][{prefix}]", payload)

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

        self._emitir_audit(
            "ETAPA3_REPOSITORY_CALL",
            {
                "arquivo_path": str(arquivo_path),
                "numero_bloco": numero_bloco,
                "diario_id": diario_id,
                "contratante": contratante,
                "contratante_normalizado": contratante_normalizado,
                "processo": processo,
                "contrato": contrato,
            },
        )
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
            print("[AUDIT][ETAPA4_SQL]", {"sql": sql.strip(), "params": params})
            cursor.execute(sql, params)
            self._emitir_audit(
                "ETAPA5_AFTER_INSERT_BEFORE_COMMIT",
                {
                    "arquivo_path": str(arquivo_path),
                    "numero_bloco": numero_bloco,
                    "contratante": contratante,
                    "contratante_normalizado": contratante_normalizado,
                },
            )
            if not hasattr(self.conn, "executed"):
                cursor.execute(
                    f"""
                    SELECT
                        contratante,
                        contratante_normalizado
                    FROM {self.table}
                    WHERE arquivo_path = %s
                      AND numero_bloco = %s
                    """,
                    (str(arquivo_path), numero_bloco),
                )
                print("[AUDIT][ETAPA5_SELECT_BEFORE_COMMIT]", cursor.fetchall())

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
