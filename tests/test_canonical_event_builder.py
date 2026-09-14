from canonical_event_builder import build_institutional_event


def test_build_institutional_event_preserva_numero_portaria_gp():
    evento = {
        "tipo_evento": "NOMEACAO",
        "numero_portaria_gp": "100/2026",
        "evidencia": {
            "diario_id": 1,
        },
    }

    resultado = build_institutional_event(evento, evento_id=10)

    assert resultado["event"]["numero_portaria_gp"] == "100/2026"