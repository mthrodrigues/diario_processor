import pytest

from taxonomy.relation_resolver import resolver_relacao_evento
from taxonomy.event_taxonomy import DESIGNACAO_FISCAL, DESIGNADO_PARA

def test_resolver_designacao_fiscal_mapeia_para_designado_para():
    assert resolver_relacao_evento(DESIGNACAO_FISCAL) == DESIGNADO_PARA.lower()
