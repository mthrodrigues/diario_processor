from taxonomy.event_taxonomy import (
    EVENT_RELATION_TYPES
)

import ecosystem_imports  # noqa: F401

from institutional_contracts.ontology.relationship_types import (
    RELATED_TO,
    normalize_relationship_type,
)


def resolver_relacao_evento(tipo_evento):

    if not tipo_evento:
        return RELATED_TO

    relationship_type = EVENT_RELATION_TYPES.get(
        tipo_evento.lower(),
        EVENT_RELATION_TYPES.get(tipo_evento, RELATED_TO)
    )

    return normalize_relationship_type(relationship_type)
