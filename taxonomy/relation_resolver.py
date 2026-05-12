from taxonomy.event_taxonomy import (
    EVENT_RELATION_TYPES
)


def resolver_relacao_evento(tipo_evento):

    if not tipo_evento:
        return "RELACIONADO_A"

    return EVENT_RELATION_TYPES.get(
        tipo_evento.lower(),
        "RELACIONADO_A"
    )