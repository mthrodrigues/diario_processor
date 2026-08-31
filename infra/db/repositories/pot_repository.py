from datetime import datetime

from config import get_postgres_config
from infra.db.migrations.runner import quote_ident


class PotRepository:
    def __init__(self, conn, schema=None):
        self.conn = conn
        self.schema = quote_ident(
            schema or get_postgres_config().schema
        )
        self.table = f"{self.schema}.pot_beneficiarios"

    def salvar_registros(
        self,
        publicacao_id,
        registros,
    ):
        if not registros:
            return 0

        with self.conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {self.table} (
                    publicacao_id,
                    numero,
                    beneficiario,
                    unidade,
                    horario_atuacao,
                    area_aprendizado,
                    data_inclusao,
                    data_desligamento,
                    substituicao,
                    texto_bruto,
                    criado_em
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """

            quantidade = 0

            for registro in registros:
                params = (
                    publicacao_id,
                    registro.get("numero"),
                    registro.get("beneficiario"),
                    registro.get("unidade"),
                    registro.get("horario_atuacao"),
                    registro.get("area_aprendizado"),
                    _converter_data(
                        registro.get("data_inclusao")
                    ),
                    _converter_data(
                        registro.get("data_desligamento")
                    ),
                    registro.get("substituicao"),
                    registro.get("texto_bruto"),
                    datetime.now(),
                )

                cursor.execute(sql, params)
                quantidade += 1

        return quantidade

    def substituir_registros(
        self,
        publicacao_id,
        registros,
    ):
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
                    numero,
                    beneficiario,
                    unidade,
                    horario_atuacao,
                    area_aprendizado,
                    data_inclusao,
                    data_desligamento,
                    substituicao,
                    texto_bruto,
                    criado_em
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """

            quantidade = 0

            for registro in registros:
                params = (
                    publicacao_id,
                    registro.get("numero"),
                    registro.get("beneficiario"),
                    registro.get("unidade"),
                    registro.get("horario_atuacao"),
                    registro.get("area_aprendizado"),
                    _converter_data(
                        registro.get("data_inclusao")
                    ),
                    _converter_data(
                        registro.get("data_desligamento")
                    ),
                    registro.get("substituicao"),
                    registro.get("texto_bruto"),
                    datetime.now(),
                )

                cursor.execute(sql, params)
                quantidade += 1

        return quantidade       

def _converter_data(valor):
    if not valor:
        return None

    if hasattr(valor, "year"):
        return valor

    try:
        dia, mes, ano = valor.strip().split("/")
        return f"{ano}-{mes}-{dia}"
    except (AttributeError, ValueError):
        return None

def substituir_registros(
    self,
    publicacao_id,
    registros,
):
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
                numero,
                beneficiario,
                unidade,
                horario_atuacao,
                area_aprendizado,
                data_inclusao,
                data_desligamento,
                substituicao,
                texto_bruto,
                criado_em
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """

        quantidade = 0

        for registro in registros:
            params = (
                publicacao_id,
                registro.get("numero"),
                registro.get("beneficiario"),
                registro.get("unidade"),
                registro.get("horario_atuacao"),
                registro.get("area_aprendizado"),
                _converter_data(
                    registro.get("data_inclusao")
                ),
                _converter_data(
                    registro.get("data_desligamento")
                ),
                registro.get("substituicao"),
                registro.get("texto_bruto"),
                datetime.now(),
            )

            cursor.execute(sql, params)
            quantidade += 1

    return quantidade