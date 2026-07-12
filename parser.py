import re


PADRAO_VALOR_MONETARIO = r'R\$\s*:?\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})'

MARCADORES_FIM_CAMPO = [
    r'OBJETO',
    r'VALOR(?:\s+(?:GLOBAL|TOTAL|ESTIMADO|CONTRATADO|DA\s+PROPOSTA|DO\s+CONTRATO))?',
    r'PRAZO',
    r'PROCESSO',
    r'CONTRATANTE',
    r'CONTRATADA',
    r'CONTRATADO',
    r'FORNECEDOR',
    r'EMPRESA',
    r'PERMITENTE',
    r'PERMISSION[ÁA]RIO',
    r'CNPJ',
    r'CPF',
    r'VIG[ÊE]NCIA',
    r'DOTA[ÇC][ÃA]O',
    r'ASSINATURA',
    r'INSCRIT[AO]\s+(?:NO|NA)\s+(?:CNPJ|CPF)',
    r'PELO\s+CONTRATANTE',
    r'PELA\s+CONTRATADA',
    r'PELO\s+PERMITENTE',
    r'PELO\s+PERMISSION[ÁA]RIO',
]

INICIOS_PUBLICACAO = [
    r'CONTRATO\b',
    r'EXTRATO\b',
    r'AVISO\b',
    r'PORTARIA\b',
    r'\d+\s*[º°]\s+TERMO\s+DE\s+APOSTILAMENTO\b',
    r'\d+\s*[º°]\s+TERMO\s+ADITIVO\b',
    r'TERMO\b',
    r'PREG[ÃA]O\b',
    r'EDITAL\b',
    r'ERRATA\b',
    r'DECRETO\b',
    r'RESOLU[ÇC][ÃA]O\b',
    r'HOMOLOGA[ÇC][ÃA]O\b',
    r'ADJUDICA[ÇC][ÃA]O\b',
    r'DISPENSA\b',
    r'INEXIGIBILIDADE\b',
    r'CHAMAMENTO\b',
    r'CONVOCA[ÇC][ÃA]O\b',
    r'BENEFICI[ÁA]RIOS?\b',
]

LINHAS_BOILERPLATE = (
    'DIÁRIO OFICIAL',
    'MUNICÍPIO DE',
    'ESTADO DO',
    'PODER EXECUTIVO',
    'CRIADO PELA LEI',
    'ANO ',
)


def _normalizar_espacos(texto):
    return " ".join(texto.split())


def _converter_valor_monetario(valor):
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")
    return float(valor)


def _limpar_campo_documental(valor):
    valor = _normalizar_espacos(valor)
    valor = re.split(
        r'\s*[-–—]\s*(?:Objeto|Valor|Prazo|Processo|Vigência)\b',
        valor,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]
    valor = re.split(
        r'\s*,?\s*inscrit[ao]\s+(?:no|na)\s+(?:CNPJ|CPF)\b',
        valor,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]
    return valor.strip(" .;:-,")


def _extrair_campo_contextual(texto, rotulos, limite=180):
    rotulos_regex = "|".join(rotulos)
    marcadores_regex = "|".join(MARCADORES_FIM_CAMPO)

    padrao = (
        rf'\b(?:{rotulos_regex})\s*:\s*'
        rf'(.+?)'
        rf'(?='
        rf'\s*[-–—]?\s*(?:{marcadores_regex})\s*:'
        rf'|\s+(?:VALOR(?:\s+(?:GLOBAL|TOTAL|ESTIMADO|CONTRATADO|DA\s+PROPOSTA|DO\s+CONTRATO))?\s*R\$|PROCESSO\s*N[°ºO\.]?)'
        rf'|$'
        rf')'
    )

    for match in re.finditer(padrao, texto, flags=re.IGNORECASE | re.DOTALL):
        candidato = _limpar_campo_documental(match.group(1))

        if not candidato or len(candidato) < 3:
            continue

        return candidato[:limite]

    return None


def _linha_continua_titulo(linha_anterior):
    if not linha_anterior:
        return False

    linha = linha_anterior.strip().upper()
    return linha.endswith((" E", " DE", " DO", " DA", " DOS", " DAS", " AO", " AOS"))


def _eh_inicio_publicacao(linha, linha_anterior=None):
    linha_limpa = linha.strip()

    if not linha_limpa:
        return False

    linha_upper = linha_limpa.upper()

    if linha_upper.startswith(LINHAS_BOILERPLATE):
        return False

    if _linha_continua_titulo(linha_anterior):
        return False

    return any(re.match(padrao, linha_upper) for padrao in INICIOS_PUBLICACAO)


def _inicio_recente_de_publicacao(bloco_atual):
    linhas = [linha for linha in bloco_atual if linha.strip()]

    if len(linhas) > 2:
        return False

    return any(_eh_inicio_publicacao(linha) for linha in linhas)


def extrair_valores(texto):
    """
    Extrai valores monetários do texto.
    Exemplo:
    R$ 1.500,00
    """

    valores = []

    matches = re.findall(PADRAO_VALOR_MONETARIO, texto, flags=re.IGNORECASE)

    for match in matches:

        try:
            valores.append(_converter_valor_monetario(match))
        except ValueError:
            continue

    return valores


def extrair_valor_principal(texto):
    """
    Extrai o valor principal com base em contexto documental.
    Quando houver múltiplos valores sem contexto claro, retorna None.
    """

    valor = r'(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})'
    padroes_contexto = [
        rf'\bvalor\s+(?:global|total|estimado|contratado|da\s+contrata[çc][ãa]o|do\s+contrato|da\s+proposta)\s*(?:de|:)?\s*R\$\s*:?\s*{valor}',
        rf'\bvalor\s*R\$\s*:?\s*{valor}',
        rf'\bvalor\s+de\s+R\$\s*:?\s*{valor}',
        rf'\bproposta\s+final\s+apresenta\s+valor\s+de\s+R\$\s*:?\s*{valor}',
        rf'\bno\s+valor\s+de\s+R\$\s*:?\s*{valor}',
    ]

    trechos = [texto]
    leia_se = list(re.finditer(r'\bleia-se\s*:?', texto, flags=re.IGNORECASE))

    if leia_se:
        trechos.insert(0, texto[leia_se[-1].end():])

    for trecho in trechos:
        for padrao in padroes_contexto:
            match = re.search(padrao, trecho, flags=re.IGNORECASE)

            if match:
                return _converter_valor_monetario(match.group(1))

    valores = extrair_valores(texto)

    if len(valores) == 1:
        return valores[0]

    return None


def extrair_vigencia(texto):
    """
    Extrai vigência ou prazo contratual usando rótulos documentais.
    """

    vigencia = _extrair_campo_contextual(
        texto,
        [
            r'VIG[ÊE]NCIA',
            r'PRAZO(?:\s+DE\s+VIG[ÊE]NCIA)?',
            r'PRAZO\s+CONTRATUAL',
        ],
        limite=220
    )

    if vigencia:
        return vigencia

    padroes = [
        r'\bvigor(?:a|ará|ara)\s+(?:por|pelo\s+prazo\s+de)\s+(.+?)(?=\.|\s+Processo\b|$)',
        r'\bcom\s+vig[êe]ncia\s+de\s+(.+?)(?=\.|\s+Processo\b|$)',
    ]

    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE | re.DOTALL)

        if match:
            return _limpar_campo_documental(match.group(1))[:220]

    return None


def extrair_objeto(texto):
    """
    Extrai objeto contratual com base no rótulo Objeto.
    """

    objeto = _extrair_campo_contextual(
        texto,
        [
            r'OBJETO',
            r'OBJETO\s+CONTRATUAL',
        ],
        limite=700
    )

    if objeto:
        return objeto

    return None


def identificar_tipo(texto):
    """
    Identifica o tipo da publicação.
    """

    linhas = [linha.strip().upper() for linha in texto.splitlines() if linha.strip()]
    inicio = "\n".join(linhas[:4])

    tipos_por_inicio = [

        # Termos numerados
        (
            r'^\d+\s*[º°]\s+TERMO\s+DE\s+APOSTILAMENTO\b',
            "apostilamento"
        ),

        (
            r'^\d+\s*[º°]\s+TERMO\s+ADITIVO\b',
            "aditivo"
        ),

        # Termos sem numeração
        (
            r'^TERMO\s+DE\s+APOSTILAMENTO\b',
            "apostilamento"
        ),

        (
            r'^TERMO\s+ADITIVO\b',
            "aditivo"
        ),

        # Demais documentos
        (r'^CONTRATO\b', "contrato"),
        (r'^TERMO\b', "termo"),
        (r'^AVISO\b', "aviso"),
        (r'^EXTRATO\b', "extrato"),
        (r'^PORTARIA\b', "portaria"),
        (r'^PREG[ÃA]O\b', "licitacao"),
        (r'^DISPENSA\b', "dispensa"),
        (r'^INEXIGIBILIDADE\b', "inexigibilidade"),
        (r'^ERRATA\b', "errata"),
        (r'^HOMOLOGA[ÇC][ÃA]O\b', "homologacao"),
        (r'^ADJUDICA[ÇC][ÃA]O\b', "adjudicacao"),
        (r'^EDITAL\b', "edital"),
    ]
    
    for padrao, tipo in tipos_por_inicio:
        if re.search(padrao, inicio):
            return tipo

    texto_upper = texto.upper()

    # ordem importa
    if "TERMO ADITIVO" in texto_upper or "ADITIVO" in inicio:
        return "aditivo"

    # =====================================================
    # FALLBACKS DOCUMENTAIS
    # Utilizados apenas quando o cabeçalho não foi suficiente.
    # Devem ser específicos para evitar superclassificação.
    # =====================================================

    if re.search(r'\bTERMO\s+ADITIVO\b', texto_upper):
        return "aditivo"

    if re.search(r'\bEXTRATO\s+DE\s+CONTRATO\b', texto_upper):
        return "extrato"

    if re.search(r'\bCONTRATO\s+ADMINISTRATIVO\b', texto_upper):
        return "contrato"

    if re.search(r'\bCONTRATO\s+N[°ºO\.]?', texto_upper):
        return "contrato"

    if "EMPENHO" in texto_upper:
        return "empenho"

    if "HOMOLOGAÇÃO" in texto_upper:
        return "homologacao"

    if "ADJUDICAÇÃO" in texto_upper:
        return "adjudicacao"

    if "PREGÃO" in texto_upper:
        return "licitacao"

    if "DISPENSA" in texto_upper:
        return "dispensa"

    if "INEXIGIBILIDADE" in texto_upper:
        return "inexigibilidade"

    if "AVISO" in texto_upper:
        return "aviso"

    if "PORTARIA" in texto_upper:
        return "portaria"

    if "TERMO" in texto_upper:
        return "termo"

    return "outro"


def extrair_processo(texto):
    """
    Extrai número de processo administrativo.
    Exemplos:
    11.302/2025
    12345/2026
    """

    numero_processo = r'(\d{1,6}(?:\.\d{3})*/\d{2,4})'
    padroes_contexto = [
        rf'\bPROCESSO\s*(?:ADMINISTRATIVO|LICITAT[ÓO]RIO)?\s*(?:N[°ºO\.]?\s*)?{numero_processo}',
        rf'\bPROC(?:ESSO)?\.\s*(?:N[°ºO\.]?\s*)?{numero_processo}',
        rf'\bPROTOCOLO\s*(?:N[°ºO\.]?\s*)?{numero_processo}',
        rf'\bMEMORANDO\s*(?:N[°ºO\.]?\s*)?{numero_processo}',
    ]

    for padrao in padroes_contexto:
        match = re.search(padrao, texto, flags=re.IGNORECASE)

        if match:
            return match.group(1)

    return None


def extrair_fornecedor(texto):
    """
    Extrai fornecedor baseado em contexto documental.
    """

    rotulos = [
        r'CONTRATADA',
        r'CONTRATADO',
        r'FORNECEDOR',
        r'EMPRESA',
        r'LOCADOR',
        r'LOCAT[ÁA]RIO',
        r'PERMISSION[ÁA]RIO',
        r'CREDOR',
        r'DETENTORA(?:\s+DA\s+ATA)?',
        r'ADJUDICAT[ÁA]RIA',
        r'VENCEDORA',
    ]

    blacklist = [
        "SECRETARIA",
        "PREFEITURA",
        "MUNICIPAL",
        "DEPARTAMENTO",
        "SUPRIMENTOS",
        "DIÁRIO OFICIAL",
        "PODER EXECUTIVO",
    ]

    candidato = _extrair_campo_contextual(texto, rotulos, limite=160)

    if not candidato:
        return None

    candidato_upper = candidato.upper()

    if any(b in candidato_upper for b in blacklist):
        return None

    if candidato_upper.startswith(("OBJETO", "PROCESSO", "VALOR", "PRAZO")):
        return None

    if len(candidato) < 5:
        return None

    return candidato


def segmentar_publicacoes(texto):
    """
    Divide o Diário em blocos/publicações.
    """

    linhas = texto.splitlines()

    blocos = []
    bloco_atual = []

    for indice, linha in enumerate(linhas):

        linha_anterior = linhas[indice - 1] if indice > 0 else None

        # inicia novo bloco
        if _eh_inicio_publicacao(linha, linha_anterior) and not _inicio_recente_de_publicacao(bloco_atual):

            # salva bloco anterior
            if bloco_atual:
                blocos.append("\n".join(bloco_atual))

            bloco_atual = [linha]

        else:
            bloco_atual.append(linha)

    # adiciona último bloco
    if bloco_atual:
        blocos.append("\n".join(bloco_atual))

    # remove vazios
    blocos = [b.strip() for b in blocos if b.strip()]

    return blocos


def extrair_contrato(texto):
    """
    Extrai número de contrato.
    """

    padroes = [
        r'\bCONTRATO(?:\s+ADMINISTRATIVO|\s+DE\s+.{1,80}?)?\s*N[°ºO\.]?\s*([\dA-Z\.\-\/]+)',
        r'\bEXTRATO\s+DE\s+CONTRATO\s*N[°ºO\.]?\s*([\d\.\-\/]+)',
        r'\bTERMO\s+DE\s+.{3,120}?\s+N[°ºO\.]?\s*([\d\.\-\/]+)',
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def extrair_cnpj(texto):
    """
    Extrai CNPJ do texto.
    """

    padrao = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'

    match = re.search(padrao, texto)

    if match:
        return match.group(0)

    return None


def extrair_contratante(texto):
    """
    Extrai contratante baseado em contexto documental.
    """

    rotulos = [
        r'CONTRATANTE',
        r'PERMITENTE',
        r'[ÓO]RG[ÃA]O\s*GERENCIADOR',
    ]

    contratante = _extrair_campo_contextual(texto, rotulos, limite=180)

    if contratante:
        return contratante

    return None
