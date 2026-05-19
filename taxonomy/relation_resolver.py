from taxonomy.event_taxonomy import (
    EVENT_RELATION_TYPES
)

# =====================================================
# RELATION TYPES
# =====================================================

RELATED_TO = "related_to"


def normalize_relationship_type(value):

    if not value:
        return RELATED_TO

    return str(value).strip().lower()


def resolver_relacao_evento(tipo_evento):

    if not tipo_evento:
        return RELATED_TO

    relationship_type = EVENT_RELATION_TYPES.get(
        tipo_evento.lower(),
        EVENT_RELATION_TYPES.get(
            tipo_evento,
            RELATED_TO
        )
    )

    return normalize_relationship_type(
        relationship_type
    )