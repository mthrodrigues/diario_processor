from config import get_postgres_config
from infra.db.migrations.runner import quote_ident


class PublicacaoProcessoRepository:
    def __init__(self, conn, schema=None):
        self.conn = conn
        self.schema = quote_ident(schema or get_postgres_config().schema)
        self.table = f"{self.schema}.publicacao_processos"

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
                    processo_id,
                    evidencia_textual,
                    ordem_no_texto
                ) VALUES (%s, %s, %s, %s)
            """

            for registro in registros:
                cursor.execute(
                    sql,
                    (
                        publicacao_id,
                        registro["processo_id"],
                        registro["evidencia_textual"],
                        registro["ordem_no_texto"],
                    ),
                )

        return len(registros)