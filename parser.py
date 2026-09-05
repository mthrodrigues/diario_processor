import re
from dataclasses import replace


PADRAO_VALOR_MONETARIO = r'R\$\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)'

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
    r'CONTRATO(?:\s+(?:ADMINISTRATIVO|DE\s+LOCAÇÃO))?\s+N[º°O.]?\s*\S+',
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

RE_BLOCO_AUTENTICACAO = re.compile(
    r"""
    Para\s+verificar\s+a\s+autenticidade
    .*?
    (?=
        DIÁRIO\s+OFICIAL\s+ELETRÔNICO
        |
        \Z
    )
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

def _normalizar_espacos(texto):
    return " ".join(texto.split())


def _converter_valor_monetario(valor):
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")
    return float(valor)

def _remover_bloco_autenticacao(valor: str) -> str:
    """
    Remove blocos de autenticação inseridos pelo OCR no meio de um campo,
    preservando o conteúdo útil após o rodapé.
    """
    if not valor:
        return ""

    return RE_BLOCO_AUTENTICACAO.sub("", valor).strip()

def _eh_cabecalho_diario(linhas, indice):
    if indice + 5 >= len(linhas):
        return False

    bloco = [
        linhas[indice + offset].strip()
        for offset in range(6)
    ]

    return (
        bloco[0].upper() == "DIÁRIO OFICIAL ELETRÔNICO"
        and bloco[1].upper() == "MUNICÍPIO DE TERESÓPOLIS"
        and bloco[2].upper() == "ESTADO DO RIO DE JANEIRO"
        and bloco[3].upper() == "PODER EXECUTIVO MUNICIPAL"
        and bloco[4].upper().startswith("CRIADO PELA LEI MUNICIPAL")
        and re.search(
            r"EDIÇÃO\s+\d+.*PÁG\.\s*\d+\s+DE\s+\d+",
            bloco[5],
            flags=re.IGNORECASE,
        )
    )


def _remover_cabecalhos_repetidos(texto):
    if not texto:
        return ""

    linhas = texto.splitlines()

    resultado = []
    ocorrencia = 0
    i = 0

    while i < len(linhas):

        if _eh_cabecalho_diario(linhas, i):
            ocorrencia += 1

            if ocorrencia == 1:
                resultado.extend(linhas[i:i + 6])

            i += 6
            continue

        resultado.append(linhas[i])
        i += 1

    return "\n".join(resultado)

def sanear_texto_pdf(texto):
    """
    Remove resíduos textuais inequivocamente não documentais
    inseridos pelo PDF/OCR.

    Nesta primeira etapa, remove apenas blocos de autenticação
    digital e cabeçalhos físicos repetidos das páginas seguintes.

    Preserva o primeiro cabeçalho do Diário, pois ele contém
    a informação necessária para rastreabilidade da data de publicação.
    """

    if not texto:
        return ""

    texto = _remover_bloco_autenticacao(texto)
    texto = _remover_cabecalhos_repetidos(texto)

    return texto


def sanear_texto_paginado(texto_paginado):
    """Aplica o saneamento legado sem perder a proveniência das linhas."""
    linhas = list(texto_paginado.linhas)
    incluir = [True] * len(linhas)
    em_bloco_autenticacao = False

    for indice, linha in enumerate(linhas):
        if em_bloco_autenticacao:
            if linha.texto.upper() == "DIÁRIO OFICIAL ELETRÔNICO":
                em_bloco_autenticacao = False
            else:
                incluir[indice] = False
                continue

        if re.search(
            r"Para\s+verificar\s+a\s+autenticidade",
            linha.texto,
            flags=re.IGNORECASE,
        ):
            incluir[indice] = False
            em_bloco_autenticacao = True

    ocorrencias_cabecalho = 0
    indice = 0

    while indice < len(linhas):
        textos = [linha.texto for linha in linhas]

        if _eh_cabecalho_diario(textos, indice):
            ocorrencias_cabecalho += 1

            if ocorrencias_cabecalho > 1:
                for posicao in range(indice, indice + 6):
                    incluir[posicao] = False

            indice += 6
            continue

        indice += 1

    return type(texto_paginado)(
        tuple(
            replace(
                linha,
                incluir_no_texto_saneado=incluir[indice],
            )
            for indice, linha in enumerate(linhas)
        )
    )


def serializar_texto_paginado(texto_paginado):
    """Serializa somente as linhas mantidas pelo saneamento."""
    return "\n".join(
        linha.texto
        for linha in texto_paginado.linhas
        if linha.incluir_no_texto_saneado
    )

def _limpar_campo_documental(valor):
    if not valor:
        return ""

    valor = _remover_bloco_autenticacao(valor)

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
        rf'\b(?:{rotulos_regex})(?:\s*:\s*|\s*[-–—]\s*|(?:\r?\n)+\s*)'
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

def _linha_continua_frase(linha_anterior):
    """
    Indica que a linha anterior termina uma frase incompleta,
    portanto a próxima linha não pode iniciar uma nova publicação.
    """

    if not linha_anterior:
        return False

    linha = linha_anterior.strip().lower()

    return linha.endswith((
        " no",
        " na",
        " nos",
        " nas",
        " do",
        " da",
        " dos",
        " das",
        " de",
        " o",
        " e",
    ))

def _eh_inicio_publicacao(linha, linha_anterior=None):
    linha_limpa = linha.strip()

    if not linha_limpa:
        return False

    linha_upper = linha_limpa.upper()

    if linha_upper.startswith(LINHAS_BOILERPLATE):
        return False

    #
    # Continuação de título
    #
    if _linha_continua_titulo(linha_anterior):
        return False

    #
    # Continuação de frase
    #
    if _linha_continua_frase(linha_anterior):
        return False

    #
    # Continuação de corrigenda
    #
    if linha_anterior:
        linha_anterior_upper = linha_anterior.strip().upper()

        if linha_anterior_upper.startswith((
            "ONDE SE LÊ:",
            "ONDE-SE LÊ:",
            "ONDE SE LE:",
            "ONDE-SE LE:",
            "LEIA-SE:",
            "LEIA SE:",
            "LEIA-SE",
            "LEIA SE",
        )):
            return False

    #
    # Cabeçalhos de tabelas de contratos
    #
    if re.match(r"CONTRATO\s+N[º°O.]?:", linha_upper):
        return False

    if re.match(r"CONTRATO\s+N[º°O.]?\s*:", linha_upper):
        return False
    
    for padrao in INICIOS_PUBLICACAO:
        # "TERMO" genérico não deve reconhecer continuações
        # de texto iniciadas em minúsculas.
        #
        # Os padrões específicos de "TERMO ADITIVO" e
        # "TERMO DE APOSTILAMENTO" continuam sendo avaliados
        # normalmente porque aparecem antes deste padrão.
        if padrao == r'TERMO\b' and not linha_limpa.startswith("TERMO"):
            continue

        if re.match(padrao, linha_upper):
            return True

    return False

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

    valor = r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)'
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
    objeto = _extrair_campo_contextual(
        texto,
        [
            r'OBJETO',
            r'OBJETO\s+CONTRATUAL',
        ],
        limite=700
    )

    return objeto

def identificar_tipo(texto):
    """
    Identifica o tipo da publicação.
    """

    linhas = [linha.strip().upper() for linha in texto.splitlines() if linha.strip()]

    tipos_por_inicio = [

        (
            r'^CORRIGENDA\b',
            "corrigenda"
        ),

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
        (r'^DECRETO\b', "decreto"),
        (r'^RESOLU[ÇC][ÃA]O\b', "resolucao"),
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

    inicio = ""

    for indice, linha in enumerate(linhas):

        # Ignora cabeçalho físico do Diário.
        if linha.startswith(LINHAS_BOILERPLATE):
            continue

        # Ignora cabeçalho de tabela contratual.
        if re.match(r"CONTRATO\s+N[º°O.]?\s*:", linha):
            continue

        if any(re.search(padrao, linha) for padrao, _ in tipos_por_inicio):
            inicio = "\n".join(linhas[indice:indice + 4])
            break

    if not inicio:
        inicio = "\n".join(linhas[:4])

    for padrao, tipo in tipos_por_inicio:
        if re.search(padrao, inicio):
            return tipo

    texto_upper = texto.upper()

    # POT — Programa Operação Trabalho
    if (
        "BENEFICIÁRIOS DO PROGRAMA OPERAÇÃO TRABALHO" in texto_upper
        or "BENEFICIARIOS DO PROGRAMA OPERACAO TRABALHO" in texto_upper
    ):
        return "pot"

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

    if re.search(r'(?m)^\s*TERMO\b', inicio.upper()):
        return "termo"

    return "outro"

def extrair_processo(texto):
    """
    Extrai número de processo administrativo.
    Exemplos:
    11.302/2025
    12345/2026
    """

    numero_processo = r'(\d+(?:\.\d+)*(?:-\d+)?\s*/\s*\d{2,4}(?:-\d+)?)'

    padroes_contexto = [
    rf'\bPROCESSO\s*:?\s*(?:ADMINISTRATIVO|LICITAT[ÓO]RIO)?\s*(?:N\s*[°ºO\.]?\s*)?{numero_processo}',
    rf'\bPROC(?:ESSO)?\.\s*(?:N\s*[°ºO\.]?\s*)?{numero_processo}',
    ]

    for padrao in padroes_contexto:
        match = re.search(padrao, texto, flags=re.IGNORECASE)

        if match:
            return re.sub(r'\s+/', '/', match.group(1))

    return None

def extrair_fornecedor(texto):
    """
    Extrai fornecedor baseado em contexto documental.
    """

    # =====================================================
    # 1ª tentativa:
    # rótulos de alta confiança (não usa blacklist)
    # =====================================================

    rotulos_confiaveis = [
        r'(?<!PELA\s)CONTRATADA',
        r'(?<!PELO\s)CONTRATADO',
    ]

    blacklist_orgao = [
        "SECRETARIA",
        "PREFEITURA",
        "DEPARTAMENTO",
        "SUPRIMENTOS",
        "DIÁRIO OFICIAL",
        "PODER EXECUTIVO",
    ]

    candidato = _extrair_campo_contextual(
        texto,
        rotulos_confiaveis,
        limite=160
    )

    if candidato:

        candidato_upper = candidato.upper()

        if any(
            re.search(rf"\b{re.escape(b)}\b", candidato_upper)
            for b in blacklist_orgao
        ):
            return None

        if candidato_upper.startswith(("OBJETO", "PROCESSO", "VALOR", "PRAZO")):
            return None

        if len(candidato) < 5:
            return None

        return candidato

    # =====================================================
    # 2ª tentativa:
    # rótulos menos confiáveis (usa blacklist)
    # =====================================================

    rotulos_secundarios = [
        r'FORNECEDOR',
        r'EMPRESA',
        r'LOCADOR',
        r'LOCAT[ÁA]RIO',
        r'PERMISSION[ÁA]RIO',
        r'CREDOR',
        r'DETENTORA(?:\s+DA\s+ATA)?',
        r'ADJUDICAT[ÁA]RIA',
        r'VENCEDORA',
        r'CESSION[ÁA]RIO',
    ]

    candidato = _extrair_campo_contextual(
        texto,
        rotulos_secundarios,
        limite=160
    )

    if not candidato:
        return None

    candidato_upper = candidato.upper()

    if any(
        re.search(rf"\b{re.escape(b)}\b", candidato_upper)
        for b in blacklist_orgao
    ):
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

        inicio = _eh_inicio_publicacao(linha, linha_anterior)
        recente = _inicio_recente_de_publicacao(bloco_atual)

        # inicia novo bloco
        if inicio and not recente:

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


def segmentar_publicacoes_paginado(texto_paginado):
    """Segmenta linhas saneadas usando os mesmos critérios do parser legado."""
    blocos = []
    bloco_atual = []
    linhas = [
        linha
        for linha in texto_paginado.linhas
        if linha.incluir_no_texto_saneado
    ]

    for indice, linha in enumerate(linhas):
        linha_anterior = linhas[indice - 1].texto if indice > 0 else None
        inicio = _eh_inicio_publicacao(
            linha.texto,
            linha_anterior,
        )
        recente = _inicio_recente_de_publicacao(
            [item.texto for item in bloco_atual]
        )

        if inicio and not recente:
            if bloco_atual:
                blocos.append(tuple(bloco_atual))

            bloco_atual = [linha]
        else:
            bloco_atual.append(linha)

    if bloco_atual:
        blocos.append(tuple(bloco_atual))

    return blocos


def serializar_bloco_paginado(bloco):
    return "\n".join(linha.texto for linha in bloco).strip()


def extrair_contrato(texto):
    """
    Extrai número de contrato.
    """

    padroes = [
    r'\bCONTRATO(?:\s+ADMINISTRATIVO|\s+DE\s+.{1,80}?|\s+REGISTRADO\s+E\s+PUBLICADO\s+SOB\s+O)?\s*N(?:\s*[°ºO])?\.?\s*([\dA-Z.\-/]+)',

    r'\bEXTRATO\s+DE\s+CONTRATO\s*N[°ºO\.]?\s*([\d\.\-\/]+)',

    r'\bTERMO\s+DE\s+.{3,120}?\s+N[°ºO\.]?\s*([\d\.\-\/]+)',

    r'\bTERMO\s+DE\s+CESS[ÃA]O\s+DE\s+USO(?:\s+DE\s+IM[ÓO]VEL)?\s+([\dA-Z\.\-\/]+)',
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:
            contrato = match.group(1).rstrip(".,;:")
            return contrato

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
