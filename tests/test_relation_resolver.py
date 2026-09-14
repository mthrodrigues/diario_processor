import pytest

from taxonomy.relation_resolver import resolver_relacao_evento
from taxonomy.event_taxonomy import (
    DESIGNACAO_FISCAL,
    DESIGNADO_PARA,
    DESIGNACAO,
    DISPENSA,
    AUTORIZOU,
)

def test_resolver_designacao_fiscal_mapeia_para_designado_para():
    assert resolver_relacao_evento(DESIGNACAO_FISCAL) == DESIGNADO_PARA.lower()

def test_resolver_dispensa_mapeia_para_autorizou():
    assert resolver_relacao_evento(DISPENSA) == AUTORIZOU.lower()

def test_resolver_designacao_mapeia_para_designado_para():
    assert resolver_relacao_evento(DESIGNACAO) == DESIGNADO_PARA.lower()