class EntityRelationshipRepository:

    def __init__(self, conn, schema="diario"):

        self.conn = conn

        self.table = f"{schema}.relacionamentos_entidades"

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

        evento_id=None

    ):

        with self.conn.cursor() as cursor:

            cursor.execute(
                f"""
                INSERT INTO {self.table} (

                    entidade_origem_id,
                    entidade_destino_id,

                    tipo_relacao,

                    diario_id,
                    data_publicacao,
                    evento_id

                ) VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s

                )
                ON CONFLICT (
                    evento_id,
                    entidade_origem_id,
                    entidade_destino_id,
                    tipo_relacao
                ) DO UPDATE SET
                    diario_id = COALESCE(EXCLUDED.diario_id, {self.table}.diario_id),
                    data_publicacao = COALESCE(EXCLUDED.data_publicacao, {self.table}.data_publicacao)
                """,
                (
                    entidade_origem_id,
                    entidade_destino_id,

                    tipo_relacao,

                    diario_id,
                    data_publicacao,
                    
                    evento_id
                )
            )