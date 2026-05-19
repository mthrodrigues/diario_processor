def build_institutional_event(evento):

    """
    Builder simplificado e desacoplado.

    Mantém compatibilidade com o restante
    do pipeline sem depender de ontology,
    graph ou institutional_contracts.
    """

    if not evento:
        return None

    return {
        "tipo_evento": evento.get("tipo_evento"),

        "agente": evento.get("agente"),

        "entidade_origem": evento.get(
            "entidade_origem"
        ),

        "entidade_destino": evento.get(
            "entidade_destino"
        ),

        "cargo": evento.get("cargo"),

        "orgao": evento.get("orgao"),

        "contrato": evento.get("contrato"),

        "processo": evento.get("processo"),

        "valor": evento.get("valor"),

        "objeto": evento.get("objeto"),

        "evidencia": evento.get("evidencia"),
    }