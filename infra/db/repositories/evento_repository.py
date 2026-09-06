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
        publicacao_id,
        numero_evento,
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
                        data_publicacao,
                        publicacao_id,
                        numero_evento

                    ) VALUES (

                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s

                    )
                    ON CONFLICT (publicacao_id, numero_evento) DO UPDATE SET
                        tipo_evento = COALESCE(EXCLUDED.tipo_evento, {self.table}.tipo_evento),
                        agente_nome = COALESCE(EXCLUDED.agente_nome, {self.table}.agente_nome),
                        cargo = COALESCE(EXCLUDED.cargo, {self.table}.cargo),
                        orgao = COALESCE(EXCLUDED.orgao, {self.table}.orgao),
                        entidade_origem = COALESCE(EXCLUDED.entidade_origem, {self.table}.entidade_origem),
                        entidade_destino = COALESCE(EXCLUDED.entidade_destino, {self.table}.entidade_destino),
                        processo = COALESCE(EXCLUDED.processo, {self.table}.processo),
                        contrato = COALESCE(EXCLUDED.contrato, {self.table}.contrato),
                        valor = COALESCE(EXCLUDED.valor, {self.table}.valor),
                        diario_id = COALESCE(EXCLUDED.diario_id, {self.table}.diario_id),
                        numero_bloco = COALESCE(EXCLUDED.numero_bloco, {self.table}.numero_bloco),
                        evidencia_textual = COALESCE(EXCLUDED.evidencia_textual, {self.table}.evidencia_textual),
                        data_publicacao = COALESCE(EXCLUDED.data_publicacao, {self.table}.data_publicacao)
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

                        publicacao_id,

                        numero_evento,
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
                    ON CONFLICT (evento_id, entidade_id, papel) DO NOTHING
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