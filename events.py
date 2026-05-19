import re

import ecosystem_imports  # noqa: F401

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


def extrair_nome(texto):

    padroes = [
        r"NOMEAR\s+([A-ZÀ-Ú\s]+)",
        r"EXONERAR\s+([A-ZÀ-Ú\s]+)",
    ]

    for padrao in padroes:

        match = re.search(padrao, texto, re.IGNORECASE)

        if match:
            nome = match.group(1).strip()

            nome = re.split(
                r"\s+(CPF|matrícula|matricula|para|no cargo)",
                nome,
                flags=re.IGNORECASE
            )[0]

            return nome.strip()

    return None


def limpar_nome(nome):

    if not nome:
        return None

    nome = re.split(
        r"\s+(CPF|matrícula|matricula|para|no cargo|símbolo|lotado)",
        nome,
        flags=re.IGNORECASE
    )[0]

    return nome.strip(" ,.-")


def extrair_agente_publico(texto):

    padroes = [

        # =====================================================
        # COM MATRÍCULA
        # =====================================================

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?),\s*matr[ií]cula",

        # =====================================================
        # PARA EXERCER
        # =====================================================

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?)\s*,?\s*para exercer",

        # =====================================================
        # PARA INTEGRAR
        # =====================================================

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?)\s*,?\s*para integrar",

        # =====================================================
        # NOMEAR DIRETO
        # =====================================================

        r"NOMEAR(?:\s+nos\s+termos.*?,)?\s*([A-ZÀ-Ú\s]+?)\s+para",

        # =====================================================
        # EXONERAR DIRETO
        # =====================================================

        r"EXONERAR(?:\s+nos\s+termos.*?,)?\s*([A-ZÀ-Ú\s]+?)\s+do\s+Cargo",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            nome = match.group(1)

            nome = re.sub(r"\s+", " ", nome)

            nome = nome.strip(" ,.-")

            # Evita lixo institucional
            if len(nome.split()) < 2:
                continue

            if "LEI" in nome.upper():
                continue

            if "COMPLEMENTAR" in nome.upper():
                continue

            return nome

    return None


def extrair_cargo(texto):

    padroes = [

        r"Cargo em Comissão de\s+([A-ZÀ-Ú\s]+?),\s*Símbolo",

        r"cargo\s+de\s+([A-ZÀ-Ú\s]+?)(?:,|\.)",

        r"função\s+de\s+([A-ZÀ-Ú\s]+?)(?:,|\.)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            cargo = match.group(1)

            cargo = re.sub(r"\s+", " ", cargo)

            return cargo.strip(" ,.-")

    return None


def extrair_orgao(texto):

    match = re.search(
        r"(SECRETARIA MUNICIPAL [A-ZÀ-Ú\s]+)",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip(" ,.-")

    return None


def segmentar_sub_eventos(texto):

    partes = re.split(
        r"(PORTARIA\s+GP\s+N[º°]\s*\d+/\d+)",
        texto,
        flags=re.IGNORECASE
    )

    subeventos = []

    atual = ""

    for parte in partes:

        if re.search(r"PORTARIA\s+GP\s+N[º°]", parte, re.IGNORECASE):

            if atual.strip():
                subeventos.append(atual.strip())

            atual = parte

        else:
            atual += " " + parte

    if atual.strip():
        subeventos.append(atual.strip())

    return subeventos


def extrair_eventos_bloco(
    metadados,
    texto_bloco,
    diario_id=None,
    numero_bloco=None
):

    eventos = []

    tipo = metadados.get("tipo")

    subeventos = segmentar_sub_eventos(texto_bloco)

    print("\nSUBEVENTOS IDENTIFICADOS:")
    print(len(subeventos))

    for subevento in subeventos:

        subevento_upper = subevento.upper()

        # =====================================================
        # EVENTO: CONTRATAÇÃO
        # =====================================================

        if tipo in ["contrato", "extrato"]:

            fornecedor = metadados.get("fornecedor_normalizado")

            contratante = metadados.get("contratante_normalizado")

            evento = {
                "tipo_evento": PUBLIC_CONTRACT,

                "entidade_origem": {
                    "tipo": PUBLIC_AGENCY,
                    "nome": contratante
                },

                "entidade_destino": {
                    "tipo": COMPANY,
                    "nome": fornecedor
                },

                "contrato": metadados.get("contrato"),

                "processo": metadados.get("processo"),

                "valor": metadados.get("valor_principal"),

                "objeto": metadados.get("objeto"),

                "evidencia": {
                    "diario_id": diario_id,
                    "numero_bloco": numero_bloco,
                    "texto": subevento[:1000]
                }
            }

            eventos.append(evento)

        # =====================================================
        # EVENTO: NOMEAÇÃO
        # =====================================================

        if "NOMEAR" in subevento_upper:

            agente = extrair_agente_publico(subevento)

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": APPOINTMENT,

                "agente": {
                    "tipo": PERSON,
                    "nome": agente
                },

                "cargo": cargo,

                "orgao": orgao,

                "evidencia": {
                    "diario_id": diario_id,
                    "numero_bloco": numero_bloco,
                    "texto": subevento[:1000]
                }
            }

            eventos.append(evento)

        # =====================================================
        # EVENTO: EXONERAÇÃO
        # =====================================================

        if "EXONERAR" in subevento_upper:

            agente = extrair_agente_publico(subevento)

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": EXONERATION,

                "agente": {
                    "tipo": PERSON,
                    "nome": agente
                },

                "cargo": cargo,

                "orgao": orgao,

                "evidencia": {
                    "diario_id": diario_id,
                    "numero_bloco": numero_bloco,
                    "texto": subevento[:1000]
                }
            }

            eventos.append(evento)

    return eventos
