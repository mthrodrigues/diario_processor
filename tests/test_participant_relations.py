import pytest
from unittest.mock import MagicMock

from taxonomy.relation_resolver import resolver_relacao_evento
from taxonomy.event_taxonomy import DESIGNACAO_FISCAL, DESIGNADO_PARA


def _run_participant_relations(evento, entity_repo, rel_repo, diario_id=1, data_publicacao=None, evento_id=99):
    """Helper replicating the persistence fragment from main.py for testing purposes."""
    orgao_nome = evento.get("orgao")
    if not orgao_nome:
        return
    entidade_orgao_id = entity_repo.obter_ou_criar("ORGAO_PUBLICO", orgao_nome)
    participantes = evento.get("participantes", [])
    if participantes:
        for participante in participantes:
            p_nome = (
                participante.get("nome")
                if isinstance(participante, dict)
                else participante
            )
            if p_nome:
                p_id = entity_repo.obter_ou_criar("PESSOA", p_nome)
                tipo_relacao = resolver_relacao_evento(evento["tipo_evento"]).lower()
                rel_repo.criar_relacao(
                    p_id,
                    entidade_orgao_id,
                    tipo_relacao,
                    diario_id=diario_id,
                    data_publicacao=data_publicacao,
                    evento_id=evento_id,
                )
    # singular agente path (kept for compatibility – not exercised in these tests)
    agente = evento.get("agente")
    agente_nome = agente.get("nome") if isinstance(agente, dict) else None
    if agente_nome:
        entidade_pessoa_id = entity_repo.obter_ou_criar("PESSOA", agente_nome)
        rel_repo.criar_relacao(
            entidade_pessoa_id,
            entidade_orgao_id,
            resolver_relacao_evento(evento["tipo_evento"]).lower(),
            diario_id=diario_id,
            data_publicacao=data_publicacao,
            evento_id=evento_id,
        )


def test_multiple_participants_creates_two_relations():
    evento = {
        "tipo_evento": DESIGNACAO_FISCAL,
        "participantes": [{"nome": "Alice"}, {"nome": "Bob"}],
        "orgao": "ORGÃO X",
    }
    entity_repo = MagicMock()
    entity_repo.obter_ou_criar.side_effect = lambda tipo, nome: {"Alice": 10, "Bob": 20, "ORGÃO X": 99}[nome]
    rel_repo = MagicMock()
    _run_participant_relations(evento, entity_repo, rel_repo)
    assert rel_repo.criar_relacao.call_count == 2
    tipo = DESIGNADO_PARA.lower()
    rel_repo.criar_relacao.assert_any_call(10, 99, tipo, diario_id=1, data_publicacao=None, evento_id=99)
    rel_repo.criar_relacao.assert_any_call(20, 99, tipo, diario_id=1, data_publicacao=None, evento_id=99)


def test_single_participant_creates_one_relation():
    evento = {
        "tipo_evento": DESIGNACAO_FISCAL,
        "participantes": [{"nome": "Carol"}],
        "orgao": "ORGÃO Y",
    }
    entity_repo = MagicMock()
    entity_repo.obter_ou_criar.side_effect = lambda tipo, nome: {"Carol": 30, "ORGÃO Y": 88}[nome]
    rel_repo = MagicMock()
    _run_participant_relations(evento, entity_repo, rel_repo)
    assert rel_repo.criar_relacao.call_count == 1
    rel_repo.criar_relacao.assert_called_once_with(
        30,
        88,
        DESIGNADO_PARA.lower(),
        diario_id=1,
        data_publicacao=None,
        evento_id=99,
    )


def test_no_orgao_creates_no_relation():
    evento = {
        "tipo_evento": DESIGNACAO_FISCAL,
        "participantes": [{"nome": "Dave"}],
        # orgao missing
    }
    entity_repo = MagicMock()
    rel_repo = MagicMock()
    _run_participant_relations(evento, entity_repo, rel_repo)
    rel_repo.criar_relacao.assert_not_called()

