class EntityRelationshipRepository:

    def __init__(self, conn, schema="diario"):

        self.conn = conn

        self.table = f"{schema}.entity_relationships"

    # =====================================================
    # CRIAR RELAÇÃO
    # =====================================================

    def criar_relacao(

        self,

        entidade_origem_id,
        entidade_destino_id,

        tipo_relacao,

        diario_id=None,
        data_publicacao=None,

    ):

        with self.conn.cursor() as cursor:

            cursor.execute(
                f"""
                INSERT INTO {self.table} (

                    entidade_origem_id,
                    entidade_destino_id,

                    tipo_relacao,

                    diario_id,
                    data_publicacao

                ) VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    %s

                )
                """,
                (
                    entidade_origem_id,
                    entidade_destino_id,

                    tipo_relacao,

                    diario_id,
                    data_publicacao
                )
            )