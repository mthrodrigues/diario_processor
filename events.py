import re

from parser import extrair_contrato

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

        r"(?:servidor|servidora)?\s*([A-ZÀ-Ú\s]+?)\s*,?\s*matr[ií]cula",

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
# EXTRAÇÃO DE MÚLTIPLOS PARTICIPANTES
# =====================================================

def extrair_participantes_cacs_fundeb(texto):
    padrao = r"(?:Titular|Suplente):\s*([^\n\r]+)"
    matches = re.findall(padrao, texto, flags=re.IGNORECASE)
    if not matches:
        return []

    participantes = []
    nomes_vistos = set()

    for item in matches:
        nome = item.strip(" ,.-")
        nome = re.sub(r"\s+", " ", nome)
        if "CARGO VAGO" in nome.upper() or nome.upper() == "VAGO":
            continue
        nome = re.split(
            r"\s+(?:CPF|matr[ií]cula|matricula)",
            nome,
            flags=re.IGNORECASE
        )[0].strip()
        if len(nome.split()) < 2:
            continue
        chave = nome.upper()
        if chave not in nomes_vistos:
            nomes_vistos.add(chave)
            participantes.append({
                "tipo": PESSOA,
                "nome": nome
            })

    return participantes


def extrair_servidores_designados(texto):
    padrao = (
        r"NOMEAR(?:\s*,?\s+nos\s+termos.*?,)?\s*,?\s*"
        r"(?:as?\s+servidoras?|os?\s+servidores?|os?\s+funcionários?)\s+"
        r"(.+?)"
        r"(?:,\s*em\s+substitui[çc][ãa]o|\s+em\s+substitui[çc][ãa]o|,\s*como\s+respons[áa]ve(?:l|is)|\s+como\s+respons[áa]ve(?:l|is)|\s+para\s+exercer|\s+para\s+integrar|\s+para\s+acompanhar)"
    )
    match = re.search(padrao, texto, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    bloco_nomes = match.group(1)
    bloco_nomes = re.sub(
        r",?\s*matr[ií]cula\s*n?[º°]?\s*[\d.\-]+(?:\s*\d+)?",
        "",
        bloco_nomes,
        flags=re.IGNORECASE
    )

    partes = re.split(r",?\s+e\s+|,\s*", bloco_nomes, flags=re.IGNORECASE)
    participantes = []
    nomes_vistos = set()

    for parte in partes:
        nome = re.sub(r"^(?:e|ou)\s+", "", parte, flags=re.IGNORECASE).strip(" ,.-")
        nome = re.sub(r"\s+", " ", nome)
        if len(nome.split()) < 2:
            continue
        if "LEI" in nome.upper() or "COMPLEMENTAR" in nome.upper():
            continue
        chave = nome.upper()
        if chave not in nomes_vistos:
            nomes_vistos.add(chave)
            participantes.append({
                "tipo": PESSOA,
                "nome": nome
            })

    return participantes


def extrair_participantes_evento(subevento, texto_bloco=None):
    # 1. Estrutura colegiada com De: e Para: (ex.: CACS/FUNDEB)
    if re.search(r"\bDe:\s*", subevento, re.IGNORECASE) and re.search(r"\bPara:\s*", subevento, re.IGNORECASE):
        participantes = extrair_participantes_cacs_fundeb(subevento)
        if participantes:
            return participantes

    # Se o preâmbulo contiver citação a portaria anterior e a estrutura De:/Para: estiver no bloco
    if texto_bloco and re.search(r"\bDe:\s*", texto_bloco, re.IGNORECASE) and re.search(r"\bPara:\s*", texto_bloco, re.IGNORECASE):
        participantes = extrair_participantes_cacs_fundeb(texto_bloco)
        if participantes:
            return participantes

    # 2. Atos com múltiplos servidores nomeados/designados
    participantes = extrair_servidores_designados(subevento)
    if participantes:
        return participantes

    # 3. Fallback para agente singular existente
    agente = extrair_agente_publico(subevento)
    if agente:
        return [{
            "tipo": PESSOA,
            "nome": agente
        }]

    return []


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
        # ================================================
        # Formas institucionais específicas em contexto
        # contratual: primeiro as mais específicas
        # ================================================

        r"firmado entre o Município de Teresópolis através da\s+(Procuradoria Geral do Município)",

        r"através da\s+(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| e o | e a | firmado | celebrado |$)",

        r"através do\s+(Fundo Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| e o | e a | firmado | celebrado |$)",

        r"firmado entre a\s+(Secretaria de Obras e Serviços Públicos)",

        r"\bna\s+(Procuradoria Geral(?: do Município)?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"\bda\s+(Procuradoria Geral(?: do Município)?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        # ================================================
        # Formas institucionais diretas
        # ================================================

        r"firmado entre a\s+(Prefeitura Municipal de Teresópolis)",

        r"firmado entre o\s+(Município de Teresópolis)(?=\s+e\s+)",

        # ================================================
        # Padrões existentes
        # ================================================

        r"(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"na\s+(Secretaria Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",

        r"\bo\s+(Fundo Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=\s+e\s+(?:(?-i:[ao])\s+)?(?-i:[A-ZÀ-Ú])|\s*,|\s+cujo objeto|\s+que tem por objeto|\s+com efeitos|\s+a partir|$)",

        r"do\s+(Fundo Municipal(?: de)? [A-ZÀ-Ú\s]+?)(?=,|\.| com efeitos| a partir| e o | e a | através | firmado | celebrado |$)",
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

    for subevento in subeventos:

        evento = None

        # Dá truncate no subevento para o processamento do evento
        subevento = subevento[:2000]
        # Dá upper na versão do evento usado para o tipo de detecção do evento
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

            participantes = extrair_participantes_evento(subevento, texto_bloco=texto_bloco)
            agente = participantes[0]["nome"] if len(participantes) == 1 else None

            orgao = extrair_orgao(subevento)

            instrumento = extrair_contrato(subevento)

            evento = {
                "tipo_evento": DESIGNACAO_FISCAL,

                "agente": {
                    "tipo": PESSOA,
                    "nome": agente
                },

                "participantes": participantes,

                "orgao": orgao,

                "contrato": instrumento,

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

            participantes = extrair_participantes_evento(subevento, texto_bloco=texto_bloco)
            agente = participantes[0]["nome"] if len(participantes) == 1 else None

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": NOMEACAO,

                "agente": {
                    "tipo": PESSOA,
                    "nome": agente
                },

                "participantes": participantes,

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

            participantes = extrair_participantes_evento(subevento, texto_bloco=texto_bloco)
            agente = participantes[0]["nome"] if len(participantes) == 1 else None

            cargo = extrair_cargo(subevento)

            orgao = extrair_orgao(subevento)

            evento = {
                "tipo_evento": EXONERACAO,

                "agente": {
                    "tipo": PESSOA,
                    "nome": agente
                },

                "participantes": participantes,

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