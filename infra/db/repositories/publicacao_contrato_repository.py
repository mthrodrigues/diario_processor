from infra.db.migrations.runner import quote_ident
from config import get_postgres_config
from normalizer import normalize_contrato

class PublicacaoContratoRepository:
    def __init__(self, conn, schema=None):
        self.conn = conn
        self.schema = quote_ident(
            schema or get_postgres_config().schema
        )
        self.table = f"{self.schema}.publicacao_contratos"

    def obter_contrato_id(self, contrato):
        contrato_normalizado = normalize_contrato(contrato)

        if contrato_normalizado is None:
            return None

        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id
                FROM {self.schema}.contratos
                WHERE contrato_normalizado = %s
                """,
                (contrato_normalizado,),
            )
            resultado = cursor.fetchone()

        return resultado[0] if resultado else None

    def substituir_registros(self, publicacao_id, registros):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM {self.table}
                WHERE publicacao_id = %s
                """,
                (publicacao_id,),
            )

            if not registros:
                return 0

            sql = f"""
                INSERT INTO {self.table} (
                    publicacao_id,
                    contrato_id,
                    contrato_texto,
                    tipo_instrumento,
                    contexto_documental,
                    evidencia_textual,
                    ordem_no_texto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            for registro in registros:
                cursor.execute(
                    sql,
                    (
                        publicacao_id,
                        registro["contrato_id"],
                        registro["contrato_texto"],
                        registro["tipo_instrumento"],
                        registro["contexto_documental"],
                        registro["evidencia_textual"],
                        registro["ordem_no_texto"],
                    ),
                )

        return len(registros)