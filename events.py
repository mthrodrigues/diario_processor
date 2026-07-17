import re

from taxonomy.entity_taxonomy import (

    EMPRESA,
    PESSOA,
    ORGAO_PUBLICO
)

from taxonomy.event_taxonomy import (

    NOMEACAO,
    EXONERACAO,
    CONTRATACAO,
    DESIGNACAO_FISCAL
)


# =====================================================
# EXTRAÇÃO DE NOME
# =====================================================

def extrair_nome(texto):

    padroes = [
        r"NOMEAR\s+([A-ZÀ-Ú\s]+)",
        r"EXONERAR\s+([A-ZÀ-Ú\s]+)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if match:

            nome = match.group(1).strip()

            nome = re.split(
                r"\s+(CPF|matrícula|matricula|para|no cargo)",
                nome,
                flags=re.IGNORECASE
            )[0]

            return nome.strip()

    return None


# =====================================================
# LIMPEZA DE NOME
# =====================================================

def limpar_nome(nome):

    if not nome:
        return None

    nome = re.split(
        r"\s+(CPF|matrícula|matricula|para|no cargo|símbolo|lotado)",
        nome,
        flags=re.IGNORECASE
    )[0]

    return nome.strip(" ,.-")


# =====================================================
# EXTRAÇÃO DE AGENTE PÚBLICO
# =====================================================

def extrair_agente_publico(texto):

    padroes = [

        r"NOMEAR(?:\s+nos\s+termos.*?,)?\s*([A-ZÀ-Ú\s]+?)\s+para",

        r"EXONERAR(?:\s+nos\s+termos.*?,)?\s*([A-ZÀ-Ú\s]+?)\s+do\s+Cargo",

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?),\s*matr[ií]cula",

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?)\s*,?\s*para exercer",

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?)\s*,?\s*para integrar",

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

            # =============================================
            # REMOVE PREFIXOS HUMANOS
            # =============================================

            nome = re.sub(
                r"^(o servidor|a servidora|os servidores|as servidoras)\s+",
                "",
                nome,
                flags=re.IGNORECASE
            ).strip()

            if len(nome.split()) < 2:
                continue

            if "LEI" in nome.upper():
                continue

            if "COMPLEMENTAR" in nome.upper():
                continue

            return nome

    return None


# =====================================================
# EXTRAÇÃO DE CARGO
# =====================================================

def extrair_cargo(texto):

    padroes = [

        # Cargo em comissão
        r"Cargo em Comissão de\s+(.+?)(?=,\s*Símbolo|,\s*lotad|,\s*com efeitos|\.|,|$)",

        # Cargo comum
        r"cargo\s+de\s+(.+?)(?=,\s*lotad|,\s*com efeitos|\.|,|$)",

        # Função
        r"função\s+de\s+(.+?)(?=,\s*lotad|,\s*com efeitos|\.|,|$)",

        # Exercício de função
        r"para exercer\s+o\s+Cargo\s+em\s+Comissão\s+de\s+(.+?)(?=,\s*Símbolo|,\s*lotad|,\s*com efeitos|\.|,|$)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            cargo = match.group(1)

            cargo = re.sub(
                r"\s+",
                " ",
                cargo
            )

            cargo = cargo.strip(" ,.-")

            if len(cargo) < 3:
                continue

            return cargo

    return None

# =====================================================
# LIMPEZA INSTITUCIONAL
# =====================================================

def limpar_texto_institucional(texto):

    if not texto:
        return ""

    padroes_remover = [

        r"Para verificar a autenticidade.*",
        r"Documento assinado digitalmente.*",
        r"ICP-Brasil.*",
        r"DIÁRIO OFICIAL ELETRÔNICO.*",
        r"Município de Teresópolis.*",
        r"Estado do Rio de Janeiro.*",
        r"PODER EXECUTIVO MUNICIPAL.*",
        r"Criado pela Lei Municipal.*",
        r"Ano XI - Edição.*",
        r"Chave de verificação.*",
        r"https://atos\.teresopolis.*",
    ]

    texto_limpo = texto

    for padrao in padroes_remover:

        texto_limpo = re.sub(
            padrao,
            "",
            texto_limpo,
            flags=re.IGNORECASE
        )

    texto_limpo = texto_limpo.replace("\n", " ")

    texto_limpo = re.sub(
        r"\s+",
        " ",
        texto_limpo
    )

    return texto_limpo.strip()


# =====================================================
# EXTRAÇÃO DE ÓRGÃO
# =====================================================

def extrair_orgao(texto):

    if not texto:
        return None

    texto = limpar_texto_institucional(texto)

    padroes = [

        r"(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"na\s+(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"do\s+(Fundo Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"através da\s+(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| e o | e a | firmado | celebrado |$)",

        r"através do\s+(Fundo Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| e o | e a | firmado | celebrado |$)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if match:

            orgao = match.group(1)

            orgao = re.sub(r"\s+", " ", orgao)

            orgao = orgao.strip(" ,.-")

            if "EMPRESA" in orgao.upper():
                continue

            if "LTDA" in orgao.upper():
                continue

            if "CNPJ" in orgao.upper():
                continue

            return orgao

    return None


# =====================================================
# SEGMENTAÇÃO DE SUBEVENTOS
# =====================================================

def segmentar_sub_eventos(texto):

    partes = re.split(
        r"(PORTARIA\s+GP\s+N[º°]\s*\d+/\d+)",
        texto,
        flags=re.IGNORECASE
    )

    subeventos = []

    atual = ""

    for parte in partes:

        if re.search(
            r"PORTARIA\s+GP\s+N[º°]",
            parte,
            re.IGNORECASE
        ):

            if atual.strip():
                subeventos.append(atual.strip())

            atual = parte

        else:

            atual += " " + parte

    if atual.strip():
        subeventos.append(atual.strip())

    return subeventos


# =====================================================
# EXTRAÇÃO DE EVENTOS DO BLOCO
# =====================================================

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

        evento = None

        subevento = subevento[:2000]

        subevento_upper = subevento.upper()

        # =====================================================
        # EVENTO: CONTRATAÇÃO
        # =====================================================

        if (
            tipo in ["contrato", "extrato"]
            and metadados.get("fornecedor_normalizado")
            and metadados.get("contratante_normalizado")
        ):

            fornecedor = metadados.get("fornecedor_normalizado")

            contratante = metadados.get("contratante_normalizado")

            evento = {
                "tipo_evento": CONTRATACAO,

                "entidade_origem": {
                    "tipo": ORGAO_PUBLICO,
                    "nome": contratante
                },

                "entidade_destino": {
                    "tipo": EMPRESA,
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

            print("EVENTO GERADO:", evento)

            if not evento["entidade_origem"]["nome"]:
                continue

            if not evento["entidade_destino"]["nome"]:
                continue

            eventos.append(evento)

        
        # =====================================================
        # EVENTO: DESIGNAÇÃO DE FISCAL
        # =====================================================

        if (
            "FISCALIZAÇÃO DO CONTRATO" in subevento_upper
            or "ACOMPANHAMENTO E FISCALIZAÇÃO" in subevento_upper
        ):

            agente = extrair_agente_publico(subevento)

            orgao = extrair_orgao(subevento)

            instrumento = re.search(
                r"(?:CONTRATO|TERMO DE COLABORAÇÃO|TERMO DE INCENTIVO|CONVÊNIO|ACORDO DE COOPERAÇÃO)\s*N?[º°]?\s*([0-9\./\-]+)",
                subevento,
                re.IGNORECASE
            )

            evento = {
                "tipo_evento": DESIGNACAO_FISCAL,

                "agente": {
                    "tipo": PESSOA,
                    "nome": agente
                },

                "orgao": orgao,

                "contrato": metadados.get("contrato"),

                "evidencia": {
                    "diario_id": diario_id,
                    "numero_bloco": numero_bloco,
                    "texto": subevento[:1000]
                }
            }

            eventos.append(evento)

            continue


        # =====================================================
        # EVENTO: NOMEAÇÃO
        # =====================================================

        if "NOMEAR" in subevento_upper:

            agente = extrair_agente_publico(subevento)

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": NOMEACAO,

                "agente": {
                    "tipo": PESSOA,
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

            print("EVENTO GERADO:", evento)

            eventos.append(evento)

        # =====================================================
        # EVENTO: EXONERAÇÃO
        # =====================================================

        if "EXONERAR" in subevento_upper:

            agente = extrair_agente_publico(subevento)

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": EXONERACAO,

                "agente": {
                    "tipo": PESSOA,
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