from normalizers.entity_normalizer import (
    normalize_entity_name
)


class EntityRepository:

    def __init__(self, conn, schema="diario"):

        self.conn = conn

        self.table = f"{schema}.entidades"

    # =====================================================
    # OBTER OU CRIAR ENTIDADE
    # =====================================================

    def obter_ou_criar(
        self,
        tipo_entidade,
        nome_original
    ):

        nome_normalizado = (
            normalize_entity_name(nome_original)
        )

        if not nome_normalizado:

            return None

        with self.conn.cursor() as cursor:

            # =============================================
            # BUSCA EXISTENTE
            # =============================================

            cursor.execute(
                f"""
                SELECT id
                FROM {self.table}
                WHERE tipo_entidade = %s
                  AND nome_normalizado = %s
                LIMIT 1
                """,
                (
                    tipo_entidade,
                    nome_normalizado
                )
            )

            row = cursor.fetchone()

            if row:

                return row[0]

            # =============================================
            # CRIA NOVA ENTIDADE
            # =============================================

            cursor.execute(
                f"""
                INSERT INTO {self.table} (

                    tipo_entidade,
                    nome_original,
                    nome_normalizado

                ) VALUES (

                    %s,
                    %s,
                    %s

                )
                RETURNING id
                """,
                (
                    tipo_entidade,
                    nome_original,
                    nome_normalizado
                )
            )

            entidade_id = cursor.fetchone()[0]

            return entidade_id