class EventoRepository:

    def __init__(self, conn, schema="diario"):

        self.conn = conn

        self.table = f"{schema}.eventos"

        self.rel_table = f"{schema}.evento_entidades"

    # =========================================================
    # SALVAR EVENTO
    # =========================================================

    def salvar_evento(
        self,
        evento,
        data_publicacao=None
    ):

        evidencia = evento.get("evidencia", {})

        print("\nSALVANDO EVENTO...")
        print(evento)
        print("DATA PUBLICACAO:", data_publicacao)

        try:

            with self.conn.cursor() as cursor:

                cursor.execute(
                    f"""
                    INSERT INTO {self.table} (

                        tipo_evento,
                        agente_nome,
                        cargo,
                        orgao,
                        entidade_origem,
                        entidade_destino,
                        processo,
                        contrato,
                        valor,
                        diario_id,
                        numero_bloco,
                        evidencia_textual,
                        data_publicacao

                    ) VALUES (

                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s

                    )
                    RETURNING id
                    """,
                    (
                        evento.get("tipo_evento"),

                        evento.get("agente", {}).get("nome"),

                        evento.get("cargo"),

                        evento.get("orgao"),

                        evento.get("entidade_origem", {}).get("nome"),

                        evento.get("entidade_destino", {}).get("nome"),

                        evento.get("processo"),

                        evento.get("contrato"),

                        evento.get("valor"),

                        evidencia.get("diario_id"),

                        evidencia.get("numero_bloco"),

                        evidencia.get("texto"),

                        data_publicacao,
                    )
                )

                evento_id = cursor.fetchone()[0]

                print("EVENTO SALVO:", evento_id)

                return evento_id

        except Exception as e:

            print("\nERRO AO SALVAR EVENTO:")
            print(e)

            raise

    # =========================================================
    # RELACIONAR ENTIDADE
    # =========================================================

    def relacionar_entidade(
        self,
        evento_id,
        entidade_id,
        papel
    ):

        try:

            with self.conn.cursor() as cursor:

                cursor.execute(
                    f"""
                    INSERT INTO {self.rel_table} (

                        evento_id,
                        entidade_id,
                        papel

                    ) VALUES (

                        %s,
                        %s,
                        %s

                    )
                    """,
                    (
                        evento_id,
                        entidade_id,
                        papel
                    )
                )

                print(
                    f"RELACIONAMENTO SALVO | "
                    f"evento={evento_id} "
                    f"entidade={entidade_id} "
                    f"papel={papel}"
                )

        except Exception as e:

            print("\nERRO AO RELACIONAR ENTIDADE:")
            print(e)

            raise