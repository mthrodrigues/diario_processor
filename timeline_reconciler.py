from taxonomy.event_taxonomy import EXONERACAO, NOMEACAO


LOTACAO = "LOTACAO"


class NenhumaTimelineAtivaError(RuntimeError):
    pass


class EncerramentoAmbiguoError(RuntimeError):
    pass


class TimelineReconciler:
    def __init__(self, conn, schema="diario"):
        self.conn = conn
        self.schema = schema
        self.eventos_table = f"{schema}.eventos"
        self.evento_entidades_table = f"{schema}.evento_entidades"
        self.timelines_table = f"{schema}.timelines_entidades"

    def reconciliar_unidade(self, entidade_id, orgao_entidade_id, tipo_vinculo=LOTACAO):
        eventos = self._listar_eventos_temporais(entidade_id, orgao_entidade_id)
        timelines_esperadas = self._construir_intervalos(
            eventos,
            entidade_id,
            orgao_entidade_id,
            tipo_vinculo,
        )
        self._persistir_intervalos(
            timelines_esperadas,
            entidade_id,
            orgao_entidade_id,
            tipo_vinculo,
        )

    def _listar_eventos_temporais(self, entidade_id, orgao_entidade_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    evento.id,
                    evento.tipo_evento,
                    evento.data_publicacao
                FROM {self.eventos_table} AS evento
                INNER JOIN {self.evento_entidades_table} AS agente
                    ON agente.evento_id = evento.id
                   AND agente.entidade_id = %s
                   AND agente.papel = 'AGENTE_PUBLICO'
                INNER JOIN {self.evento_entidades_table} AS orgao
                    ON orgao.evento_id = evento.id
                   AND orgao.entidade_id = %s
                   AND orgao.papel = 'ORGAO_CONTRATANTE'
                WHERE evento.tipo_evento IN (%s, %s)
                ORDER BY evento.data_publicacao, evento.id
                """,
                (entidade_id, orgao_entidade_id, NOMEACAO, EXONERACAO),
            )
            return cursor.fetchall()

    def _construir_intervalos(
        self,
        eventos,
        entidade_id,
        orgao_entidade_id,
        tipo_vinculo,
    ):
        intervalos = []
        abertos = []

        for evento_id, tipo_evento, data_evento in eventos:
            if tipo_evento == NOMEACAO:
                intervalo = {
                    "entidade_id": entidade_id,
                    "orgao_entidade_id": orgao_entidade_id,
                    "tipo_vinculo": tipo_vinculo,
                    "data_inicio": data_evento,
                    "data_fim": None,
                    "ativo": True,
                    "evento_inicio_id": evento_id,
                    "evento_fim_id": None,
                }
                intervalos.append(intervalo)
                abertos.append(intervalo)
                continue

            candidatas = [
                intervalo
                for intervalo in abertos
                if intervalo["data_inicio"] <= data_evento
            ]
            if not candidatas:
                raise NenhumaTimelineAtivaError(evento_id)
            if len(candidatas) != 1:
                raise EncerramentoAmbiguoError(evento_id)

            intervalo = candidatas[0]
            intervalo["data_fim"] = data_evento
            intervalo["evento_fim_id"] = evento_id
            intervalo["ativo"] = False
            abertos.remove(intervalo)

        return intervalos

    def _persistir_intervalos(
        self,
        intervalos,
        entidade_id,
        orgao_entidade_id,
        tipo_vinculo,
    ):
        evento_inicio_ids = [
            intervalo["evento_inicio_id"]
            for intervalo in intervalos
        ]

        with self.conn.cursor() as cursor:
            for intervalo in intervalos:
                cursor.execute(
                    f"""
                    INSERT INTO {self.timelines_table} (
                        entidade_id,
                        orgao_entidade_id,
                        tipo_vinculo,
                        data_inicio,
                        data_fim,
                        ativo,
                        evento_inicio_id,
                        evento_fim_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (evento_inicio_id) DO UPDATE SET
                        entidade_id = EXCLUDED.entidade_id,
                        orgao_entidade_id = EXCLUDED.orgao_entidade_id,
                        tipo_vinculo = EXCLUDED.tipo_vinculo,
                        data_inicio = EXCLUDED.data_inicio,
                        data_fim = EXCLUDED.data_fim,
                        ativo = EXCLUDED.ativo,
                        evento_fim_id = EXCLUDED.evento_fim_id
                    """,
                    (
                        intervalo["entidade_id"],
                        intervalo["orgao_entidade_id"],
                        intervalo["tipo_vinculo"],
                        intervalo["data_inicio"],
                        intervalo["data_fim"],
                        intervalo["ativo"],
                        intervalo["evento_inicio_id"],
                        intervalo["evento_fim_id"],
                    ),
                )

            if evento_inicio_ids:
                cursor.execute(
                    f"""
                    DELETE FROM {self.timelines_table}
                    WHERE entidade_id = %s
                      AND orgao_entidade_id = %s
                      AND tipo_vinculo = %s
                      AND NOT (evento_inicio_id = ANY(%s))
                    """,
                    (
                        entidade_id,
                        orgao_entidade_id,
                        tipo_vinculo,
                        evento_inicio_ids,
                    ),
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM {self.timelines_table}
                    WHERE entidade_id = %s
                      AND orgao_entidade_id = %s
                      AND tipo_vinculo = %s
                    """,
                    (entidade_id, orgao_entidade_id, tipo_vinculo),
                )