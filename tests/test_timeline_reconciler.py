from unittest import TestCase

from timeline_reconciler import (
    EncerramentoAmbiguoError,
    TimelineReconciler,
)


class CursorTimeline:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))
        if "SELECT" in sql:
            self.conn.resultados = list(self.conn.eventos)

    def fetchall(self):
        return self.conn.resultados


class ConexaoTimeline:
    def __init__(self, eventos):
        self.eventos = eventos
        self.resultados = []
        self.executed = []

    def cursor(self):
        return CursorTimeline(self)


class TimelineReconcilerTest(TestCase):
    def test_reconcilia_intervalo_fechado_com_upsert_e_preserva_inicio(self):
        conn = ConexaoTimeline([
            (1, "NOMEACAO", "2026-01-01"),
            (2, "EXONERACAO", "2026-02-01"),
        ])

        TimelineReconciler(conn).reconciliar_unidade(10, 20)

        sql_upsert, params_upsert = conn.executed[1]
        self.assertIn("ON CONFLICT (evento_inicio_id) DO UPDATE", sql_upsert)
        self.assertEqual(params_upsert[3], "2026-01-01")
        self.assertEqual(params_upsert[4], "2026-02-01")
        self.assertFalse(params_upsert[5])
        self.assertEqual(params_upsert[6:], (1, 2))

    def test_exoneracao_sem_abertura_observavel_nao_persiste_nem_remove_timelines(self):
        conn = ConexaoTimeline([(2, "EXONERACAO", "2026-02-01")])

        resultado = TimelineReconciler(conn).reconciliar_unidade(10, 20)

        self.assertEqual(resultado.exoneracoes_sem_abertura_observavel, (2,))
        self.assertEqual(len(conn.executed), 1)
        self.assertIn("SELECT", conn.executed[0][0])
    def test_detecta_exoneracao_ambigua(self):
        conn = ConexaoTimeline([
            (1, "NOMEACAO", "2026-01-01"),
            (2, "NOMEACAO", "2026-01-02"),
            (3, "EXONERACAO", "2026-02-01"),
        ])

        with self.assertRaises(EncerramentoAmbiguoError):
            TimelineReconciler(conn).reconciliar_unidade(10, 20)

    def test_duas_nomeacoes_sucessivas_permanecem_intervalos_distintos(self):
        conn = ConexaoTimeline([
            (1, "NOMEACAO", "2026-01-01"),
            (2, "NOMEACAO", "2026-02-01"),
        ])

        intervalos, _ = TimelineReconciler(conn)._construir_intervalos(
            conn.eventos,
            10,
            20,
            "LOTACAO",
        )

        self.assertEqual([item["evento_inicio_id"] for item in intervalos], [1, 2])
        self.assertTrue(all(item["ativo"] for item in intervalos))

    def test_nova_nomeacao_apos_exoneracao_cria_novo_intervalo_ativo(self):
        conn = ConexaoTimeline([
            (1, "NOMEACAO", "2026-01-01"),
            (2, "EXONERACAO", "2026-02-01"),
            (3, "NOMEACAO", "2026-03-01"),
        ])

        intervalos, _ = TimelineReconciler(conn)._construir_intervalos(
            conn.eventos,
            10,
            20,
            "LOTACAO",
        )

        self.assertEqual(len(intervalos), 2)
        self.assertEqual(intervalos[0]["evento_fim_id"], 2)
        self.assertFalse(intervalos[0]["ativo"])
        self.assertEqual(intervalos[1]["evento_inicio_id"], 3)
        self.assertTrue(intervalos[1]["ativo"])

    def test_alteracao_no_evento_de_fechamento_atualiza_o_intervalo_da_mesma_abertura(self):
        conn = ConexaoTimeline([
            (1, "NOMEACAO", "2026-01-01"),
            (3, "EXONERACAO", "2026-03-01"),
        ])

        intervalos, _ = TimelineReconciler(conn)._construir_intervalos(
            conn.eventos,
            10,
            20,
            "LOTACAO",
        )

        self.assertEqual(intervalos[0]["evento_inicio_id"], 1)
        self.assertEqual(intervalos[0]["data_inicio"], "2026-01-01")
        self.assertEqual(intervalos[0]["evento_fim_id"], 3)
        self.assertEqual(intervalos[0]["data_fim"], "2026-03-01")

    def test_remove_somente_aberturas_ausentes_do_conjunto_reconciliado(self):
        conn = ConexaoTimeline([(2, "NOMEACAO", "2026-02-01")])

        TimelineReconciler(conn).reconciliar_unidade(10, 20)

        sql_delete, params_delete = conn.executed[-1]
        self.assertIn("NOT (evento_inicio_id = ANY(%s))", sql_delete)
        self.assertEqual(params_delete, (10, 20, "LOTACAO", [2]))