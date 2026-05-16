from __future__ import annotations

import os
from datetime import date
from typing import Any

import ecosystem_imports  # noqa: F401

from institutional_contracts import (
    CanonicalEntity,
    CanonicalRelationship,
    Evidence,
    InstitutionalEvent,
    LineageLink,
)
from institutional_contracts.hashing import (
    hash_json,
    hash_text,
)
from institutional_contracts.ontology.entity_roles import (
    APPOINTED_PERSON,
    CONTRACTING_ORG,
    DISMISSED_PERSON,
    PUBLIC_AGENT,
    SUPPLIER,
)
from institutional_contracts.ontology.entity_types import (
    COMPANY,
    PERSON,
    PUBLIC_AGENCY,
)
from institutional_contracts.ontology.event_types import (
    APPOINTMENT,
    EXONERATION,
    PUBLIC_CONTRACT,
)
from institutional_contracts.ontology.relationship_types import (
    APPOINTED,
    CONTRACTED,
    DISMISSED,
    EXTRACTED_FROM,
)


SOURCE_URL_TEMPLATE = os.getenv(
    "DIARIO_SOURCE_URL_TEMPLATE",
    "https://atos.teresopolis.rj.gov.br/recurso/diario/editar/{id}",
)


def build_institutional_event(
    *,
    evento: dict[str, Any],
    evento_id: int,
    diario_id: int,
    numero_bloco: int,
    texto_bloco: str,
    data_publicacao: date | None,
) -> InstitutionalEvent:
    source_document_id = f"diario:{diario_id}"
    source_record_id = f"{source_document_id}:bloco:{numero_bloco}:evento:{evento_id}"
    source_url = SOURCE_URL_TEMPLATE.format(id=diario_id)
    raw_hash = hash_text(texto_bloco or "")
    normalized_hash = hash_json(evento)
    entities = _build_entities(evento)

    return InstitutionalEvent(
        event_type=evento["tipo_evento"],
        event_date=data_publicacao,
        source_system="diario_processor",
        source_reference=source_record_id,
        source_record_id=source_record_id,
        source_document_id=source_document_id,
        source_url=source_url,
        raw_hash=raw_hash,
        normalized_hash=normalized_hash,
        title=evento.get("contrato") or evento.get("cargo"),
        description=evento.get("objeto") or evento.get("cargo"),
        entities=entities,
        relationships=_build_relationships(evento),
        evidence=[
            Evidence(
                evidence_type="DOCUMENT_TEXT",
                source_system="diario_processor",
                source_reference=f"{source_document_id}:bloco:{numero_bloco}",
                description="Texto do bloco do Diario Oficial usado na extracao.",
                source_url=source_url,
                raw_text=texto_bloco[:4000] if texto_bloco else None,
                raw_hash=raw_hash,
                normalized_hash=normalized_hash,
                metadata={
                    "diario_id": diario_id,
                    "numero_bloco": numero_bloco,
                    "evento_id": evento_id,
                },
            )
        ],
        lineage=[
            LineageLink(
                source_reference=source_document_id,
                target_reference=source_record_id,
                relationship_type=EXTRACTED_FROM,
                evidence_reference=f"{source_document_id}:bloco:{numero_bloco}",
            )
        ],
        temporal_context={
            "institutional_date": (
                data_publicacao.isoformat()
                if data_publicacao
                else None
            )
        },
        extraction_context={
            "extractor": "diario_processor.events.extrair_eventos_bloco",
            "diario_id": diario_id,
            "numero_bloco": numero_bloco,
        },
        explainability={
            "summary": (
                "Evento institucional extraido de bloco documental do Diario Oficial "
                "com evidencia textual preservada."
            )
        },
        metadata={
            "processo": evento.get("processo"),
            "contrato": evento.get("contrato"),
            "valor": evento.get("valor"),
            "cargo": evento.get("cargo"),
            "orgao": evento.get("orgao"),
        },
    )


def _build_entities(evento: dict[str, Any]) -> list[CanonicalEntity]:
    entities = []

    agente_nome = (evento.get("agente") or {}).get("nome")
    if agente_nome:
        role = PUBLIC_AGENT
        if evento.get("tipo_evento") == APPOINTMENT:
            role = APPOINTED_PERSON
        elif evento.get("tipo_evento") == EXONERATION:
            role = DISMISSED_PERSON

        entities.append(
            CanonicalEntity(
                entity_type=PERSON,
                name=agente_nome,
                role=role,
                source_reference="agente",
            )
        )

    orgao_nome = evento.get("orgao") or (evento.get("entidade_origem") or {}).get("nome")
    if orgao_nome:
        entities.append(
            CanonicalEntity(
                entity_type=PUBLIC_AGENCY,
                name=orgao_nome,
                role=CONTRACTING_ORG,
                source_reference="orgao",
            )
        )

    empresa_nome = (evento.get("entidade_destino") or {}).get("nome")
    if empresa_nome:
        entities.append(
            CanonicalEntity(
                entity_type=COMPANY,
                name=empresa_nome,
                role=SUPPLIER,
                source_reference="empresa",
            )
        )

    return entities


def _build_relationships(evento: dict[str, Any]) -> list[CanonicalRelationship]:
    relationships = []
    event_type = evento.get("tipo_evento")

    if event_type == PUBLIC_CONTRACT:
        origem = (evento.get("entidade_origem") or {}).get("nome")
        destino = (evento.get("entidade_destino") or {}).get("nome")

        if origem and destino:
            relationships.append(
                CanonicalRelationship(
                    source=origem,
                    target=destino,
                    relationship_type=CONTRACTED,
                )
            )

    agente = (evento.get("agente") or {}).get("nome")
    orgao = evento.get("orgao")

    if agente and orgao and event_type == APPOINTMENT:
        relationships.append(
            CanonicalRelationship(
                source=agente,
                target=orgao,
                relationship_type=APPOINTED,
            )
        )

    if agente and orgao and event_type == EXONERATION:
        relationships.append(
            CanonicalRelationship(
                source=agente,
                target=orgao,
                relationship_type=DISMISSED,
            )
        )

    return relationships
