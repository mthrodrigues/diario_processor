from dataclasses import dataclass

import pytest

from infra.db.repositories.timeline_repository import TimelineRepository
from taxonomy.event_taxonomy import EXONERACAO, NOMEACAO


LOTACAO = "LOTACAO"
PESSOA_ID = 10
ORGAO_ID = 20


class EncerramentoAmbiguoError(RuntimeError):
    pass


@dataclass(frozen=True)
class EventoTemporal:
    id: int
    publicacao_id: int
    tipo: str
    entidade_id: int
    orgao_entidade_id: int
    data: str
    tipo_vinculo: str = LOTACAO


class ModeloTimeline:
    """Especificação de domínio para o reconciliador de produção futuro."""

    def __init__(self):
        self._eventos_por_publicacao = {}
        self._ids_por_evento_inicio = {}
        self._proximo_id = 1
        self.timelines = []
        self.exoneracoes_sem_abertura_observavel = []

    def substituir_publicacao(self, publicacao_id, eventos):
        self._eventos_por_publicacao[publicacao_id] = tuple(eventos)
        self._reconciliar()

    def _reconciliar(self):
        timelines_anteriores = {
            timeline["evento_inicio_id"]: timeline["id"]
            for timeline in self.timelines
        }
        abertas = []
        timelines = []
        exoneracoes_sem_abertura_observavel = []
        eventos = sorted(
            (
                evento
                for eventos_publicacao in self._eventos_por_publicacao.values()
                for evento in eventos_publicacao
            ),
            key=lambda evento: (evento.data, evento.id),
        )

        for evento in eventos:
            if evento.tipo == NOMEACAO:
                timeline_id = timelines_anteriores.get(evento.id)
                if timeline_id is None:
                    timeline_id = self._ids_por_evento_inicio.setdefault(
                        evento.id,
                        self._proximo_id,
                    )
                    if timeline_id == self._proximo_id:
                        self._proximo_id += 1

                timeline = {
                    "id": timeline_id,
                    "entidade_id": evento.entidade_id,
                    "orgao_entidade_id": evento.orgao_entidade_id,
                    "tipo_vinculo": evento.tipo_vinculo,
                    "data_inicio": evento.data,
                    "data_fim": None,
                    "ativo": True,
                    "evento_inicio_id": evento.id,
                    "evento_fim_id": None,
                }
                timelines.append(timeline)
                abertas.append(timeline)
                continue

            if evento.tipo != EXONERACAO:
                continue

            candidatas = [
                timeline
                for timeline in abertas
                if timeline["entidade_id"] == evento.entidade_id
                and timeline["orgao_entidade_id"] == evento.orgao_entidade_id
                and timeline["tipo_vinculo"] == evento.tipo_vinculo
                and timeline["data_inicio"] <= evento.data
            ]

            if not candidatas:
                exoneracoes_sem_abertura_observavel.append(evento.id)
                continue

            if len(candidatas) != 1:
                raise EncerramentoAmbiguoError(evento.id)

            timeline = candidatas[0]
            timeline["data_fim"] = evento.data
            timeline["evento_fim_id"] = evento.id
            timeline["ativo"] = False
            abertas.remove(timeline)

        self.exoneracoes_sem_abertura_observavel = exoneracoes_sem_abertura_observavel
        if exoneracoes_sem_abertura_observavel:
            return

        self.timelines = timelines


def nomeacao(evento_id, publicacao_id, data, entidade_id=PESSOA_ID, orgao_id=ORGAO_ID):
    return EventoTemporal(
        evento_id,
        publicacao_id,
        NOMEACAO,
        entidade_id,
        orgao_id,
        data,
    )


def exoneracao(evento_id, publicacao_id, data, entidade_id=PESSOA_ID, orgao_id=ORGAO_ID):
    return EventoTemporal(
        evento_id,
        publicacao_id,
        EXONERACAO,
        entidade_id,
        orgao_id,
        data,
    )


def assert_timeline(
    timeline,
    *,
    timeline_id,
    data_inicio,
    data_fim,
    ativo,
    evento_inicio_id,
    evento_fim_id,
):
    assert timeline == {
        "id": timeline_id,
        "entidade_id": PESSOA_ID,
        "orgao_entidade_id": ORGAO_ID,
        "tipo_vinculo": LOTACAO,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "ativo": ativo,
        "evento_inicio_id": evento_inicio_id,
        "evento_fim_id": evento_fim_id,
    }


def test_nomeacao_isolada_cria_exatamente_um_intervalo():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])

    assert len(modelo.timelines) == 1
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim=None,
        ativo=True,
        evento_inicio_id=1,
        evento_fim_id=None,
    )


def test_nomeacao_e_exoneracao_em_publicacoes_diferentes_formam_um_intervalo():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])
    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])

    assert len(modelo.timelines) == 1
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim="2026-02-01",
        ativo=False,
        evento_inicio_id=1,
        evento_fim_id=2,
    )


def test_reprocessar_nomeacao_nao_duplica_nem_reabre_intervalo_encerrado():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])
    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])

    assert len(modelo.timelines) == 1
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim="2026-02-01",
        ativo=False,
        evento_inicio_id=1,
        evento_fim_id=2,
    )


def test_reprocessar_exoneracao_nao_cria_intervalo_nem_altera_inicio():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])
    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])
    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])

    assert len(modelo.timelines) == 1
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim="2026-02-01",
        ativo=False,
        evento_inicio_id=1,
        evento_fim_id=2,
    )


def test_reprocessar_ambas_publicacoes_preserva_estado_e_id():
    modelo = ModeloTimeline()
    eventos_abertura = [nomeacao(1, 100, "2026-01-01")]
    eventos_fechamento = [exoneracao(2, 200, "2026-02-01")]

    modelo.substituir_publicacao(100, eventos_abertura)
    modelo.substituir_publicacao(200, eventos_fechamento)
    estado_esperado = list(modelo.timelines)
    modelo.substituir_publicacao(100, eventos_abertura)
    modelo.substituir_publicacao(200, eventos_fechamento)

    assert modelo.timelines == estado_esperado


def test_duas_nomeacoes_sucessivas_produzem_dois_intervalos_ativos_distintos():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])
    modelo.substituir_publicacao(200, [nomeacao(2, 200, "2026-02-01")])

    assert len(modelo.timelines) == 2
    assert [timeline["evento_inicio_id"] for timeline in modelo.timelines] == [1, 2]
    assert all(timeline["ativo"] for timeline in modelo.timelines)


def test_nomeacao_exoneracao_e_nova_nomeacao_preservam_dois_intervalos():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(100, [nomeacao(1, 100, "2026-01-01")])
    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])
    modelo.substituir_publicacao(300, [nomeacao(3, 300, "2026-03-01")])

    assert len(modelo.timelines) == 2
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim="2026-02-01",
        ativo=False,
        evento_inicio_id=1,
        evento_fim_id=2,
    )
    assert_timeline(
        modelo.timelines[1],
        timeline_id=2,
        data_inicio="2026-03-01",
        data_fim=None,
        ativo=True,
        evento_inicio_id=3,
        evento_fim_id=None,
    )


def test_exoneracao_com_duas_linhas_ativas_e_ambigua():
    modelo = ModeloTimeline()
    modelo.substituir_publicacao(
        100,
        [nomeacao(1, 100, "2026-01-01"), nomeacao(2, 100, "2026-01-02")],
    )

    with pytest.raises(EncerramentoAmbiguoError):
        modelo.substituir_publicacao(200, [exoneracao(3, 200, "2026-02-01")])

    assert len(modelo.timelines) == 2
    assert all(timeline["ativo"] for timeline in modelo.timelines)


def test_exoneracao_sem_abertura_observavel_nao_cria_intervalo():
    modelo = ModeloTimeline()

    modelo.substituir_publicacao(200, [exoneracao(2, 200, "2026-02-01")])

    assert modelo.timelines == []
    assert modelo.exoneracoes_sem_abertura_observavel == [2]


def test_reprocessamento_seletivo_tem_mesmo_estado_da_reconstrucao_integral():
    eventos_abertura = [nomeacao(1, 100, "2026-01-01")]
    eventos_fechamento = [exoneracao(2, 200, "2026-02-01")]
    seletivo = ModeloTimeline()
    integral = ModeloTimeline()

    seletivo.substituir_publicacao(100, eventos_abertura)
    seletivo.substituir_publicacao(200, eventos_fechamento)
    seletivo.substituir_publicacao(100, eventos_abertura)

    integral.substituir_publicacao(100, eventos_abertura)
    integral.substituir_publicacao(200, eventos_fechamento)

    assert seletivo.timelines == integral.timelines


def test_tres_reprocessamentos_preservam_mesma_cardinalidade_e_ids():
    modelo = ModeloTimeline()
    eventos_abertura = [nomeacao(1, 100, "2026-01-01")]
    eventos_fechamento = [exoneracao(2, 200, "2026-02-01")]

    for _ in range(3):
        modelo.substituir_publicacao(100, eventos_abertura)
        modelo.substituir_publicacao(200, eventos_fechamento)

    assert len(modelo.timelines) == 1
    assert_timeline(
        modelo.timelines[0],
        timeline_id=1,
        data_inicio="2026-01-01",
        data_fim="2026-02-01",
        ativo=False,
        evento_inicio_id=1,
        evento_fim_id=2,
    )


class CursorRegistroSql:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))


class ConexaoRegistroSql:
    def __init__(self):
        self.executed = []

    def cursor(self):
        return CursorRegistroSql(self)


def test_fechar_vinculo_atual_e_inadequado_para_contrato_de_ambiguidade():
    conn = ConexaoRegistroSql()
    repository = TimelineRepository(conn)

    repository.fechar_vinculo(PESSOA_ID, ORGAO_ID, "2026-02-01", 2)

    sql, _ = conn.executed[0]
    assert "tipo_vinculo" not in sql
    assert "evento_inicio_id" not in sql
    assert "LIMIT 1" not in sql
    assert "ativo = TRUE" in sql