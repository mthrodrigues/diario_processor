class TimelineRepository:

    def __init__(self, conn, schema="diario"):

        self.conn = conn

        self.table = f"{schema}.timelines_entidades"

    # =====================================================
    # ABRIR VÍNCULO
    # =====================================================

    def abrir_vinculo(

        self,

        entidade_id,
        orgao_entidade_id,

        tipo_vinculo,

        data_inicio,

        evento_inicio_id

    ):

        with self.conn.cursor() as cursor:

            cursor.execute(
                f"""
                INSERT INTO {self.table} (

                    entidade_id,
                    orgao_entidade_id,

                    tipo_vinculo,

                    data_inicio,

                    evento_inicio_id,

                    ativo

                ) VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE

                )
                """,
                (
                    entidade_id,
                    orgao_entidade_id,

                    tipo_vinculo,

                    data_inicio,

                    evento_inicio_id
                )
            )

    # =====================================================
    # FECHAR VÍNCULO
    # =====================================================

    def fechar_vinculo(

        self,

        entidade_id,
        orgao_entidade_id,

        data_fim,

        evento_fim_id

    ):

        with self.conn.cursor() as cursor:

            cursor.execute(
                f"""
                UPDATE {self.table}
                SET

                    data_fim = %s,

                    evento_fim_id = %s,

                    ativo = FALSE

                WHERE entidade_id = %s
                  AND orgao_entidade_id = %s
                  AND ativo = TRUE
                """,
                (
                    data_fim,
                    evento_fim_id,

                    entidade_id,
                    orgao_entidade_id
                )
            )