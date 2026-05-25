def build_institutional_event(
    evento,
    evento_id=None
):

    """
    Builder canônico institucional.

    Objetivos:

    - desacoplamento do schema interno
    - estabilidade contratual
    - versionamento
    - interoperabilidade futura
    - correlation readiness
    - explainability
    """

    if not evento:
        return None

    return {

        # ==========================================
        # VERSIONAMENTO
        # ==========================================

        "schema_version": "1.0",

        # ==========================================
        # IDENTIDADE GLOBAL
        # ==========================================

        "event_uuid": evento.get("uuid"),

        # ==========================================
        # ORIGEM
        # ==========================================

        "source": {

            "system": "DIARIO_PROCESSOR",

            "record_id": (
                str(evento_id)
                if evento_id
                else None
            ),

            "diario_id": evento.get(
                "evidencia",
                {}
            ).get("diario_id")
        },

        # ==========================================
        # EVENTO
        # ==========================================

        "event": {

            "tipo_evento": evento.get(
                "tipo_evento"
            ),

            "agente": evento.get(
                "agente"
            ),

            "entidade_origem": evento.get(
                "entidade_origem"
            ),

            "entidade_destino": evento.get(
                "entidade_destino"
            ),

            "cargo": evento.get(
                "cargo"
            ),

            "orgao": evento.get(
                "orgao"
            ),

            "contrato": evento.get(
                "contrato"
            ),

            "processo": evento.get(
                "processo"
            ),

            "valor": evento.get(
                "valor"
            ),

            "objeto": evento.get(
                "objeto"
            ),

            "evidencia": evento.get(
                "evidencia"
            ),
        }
    }