import re
import unicodedata


SUFIXOS_EMPRESARIAIS_FORTES = {
    "LTDA",
    "EIRELI",
    "SA",
}

SUFIXOS_EMPRESARIAIS_FINAIS = {
    "ME",
    "EPP",
}

DESCRITORES_EMPRESARIAIS_FINAIS = [
    ("INDUSTRIA", "QUIMICA"),
]


def _remover_acentos(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(char for char in texto_normalizado if not unicodedata.combining(char))


def _tokenizar(texto):
    texto = _remover_acentos(texto)
    texto = texto.upper()
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    tokens = texto.split()

    tokens_compactados = []
    indice = 0

    while indice < len(tokens):
        if tokens[indice] == "S" and indice + 1 < len(tokens) and tokens[indice + 1] == "A":
            tokens_compactados.append("SA")
            indice += 2
            continue

        tokens_compactados.append(tokens[indice])
        indice += 1

    return tokens_compactados


def _remover_sufixos(tokens):
    tokens_originais = list(tokens)
    tokens = [token for token in tokens if token not in SUFIXOS_EMPRESARIAIS_FORTES]

    while tokens and tokens[-1] in SUFIXOS_EMPRESARIAIS_FINAIS:
        tokens.pop()

    houve_remocao = True

    while houve_remocao:
        houve_remocao = False

        for descritor in DESCRITORES_EMPRESARIAIS_FINAIS:
            tamanho = len(descritor)

            if len(tokens) > tamanho and tuple(tokens[-tamanho:]) == descritor:
                del tokens[-tamanho:]
                houve_remocao = True
                break

    return tokens or tokens_originais


def normalize_entidade(nome):
    if nome is None:
        return None

    tokens = _tokenizar(nome)

    if not tokens:
        return None

    tokens = _remover_sufixos(tokens)
    normalizado = " ".join(tokens).strip()

    return normalizado or None


def _normalizar_fundo_municipal_unico(nome):
    if nome is None or not isinstance(nome, str):
        return None

    texto = _remover_acentos(nome)
    texto = texto.upper()
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto or "FUNDO MUNICIPAL" not in texto:
        return None

    ocorrencias = texto.count("FUNDO MUNICIPAL")
    if ocorrencias > 1:
        return None

    if re.match(r"^(?:O\s+)?FUNDO MUNICIPAL\b", texto):
        restante = texto.split("FUNDO MUNICIPAL", 1)[1].strip()
    else:
        match = re.search(
            r"\bATRAVES DO\s+FUNDO MUNICIPAL\b(.*?)(?=\s+E\s+(?:MITRA|OS|SRS|SECRETARIA|PREFEITURA|MUNICIPIO|ESTADO)\b|$)",
            texto,
        )
        if not match:
            return None
        restante = match.group(1).strip()

    if not restante:
        return None

    tokens = restante.split()
    if not tokens:
        return None

    if tokens[0] in {"DE", "DO", "DA"}:
        tokens = tokens[1:]

    if not tokens:
        return None

    if re.search(r"\bE\s+(MITRA|OS|SRS|SECRETARIA|PREFEITURA|MUNICIPIO|ESTADO)\b", " ".join(tokens)):
        return None

    if len(tokens) >= 2 and tokens[-2:] == ["DE", "TERESOPOLIS"]:
        if "MUNICIPIO" in tokens[:-2]:
            return None
        tokens = tokens[:-2]
    elif "MUNICIPIO" in tokens and "TERESOPOLIS" in tokens:
        return None

    if not tokens:
        return None

    return "FUNDO MUNICIPAL " + " ".join(tokens)


def normalize_fornecedor(nome):
    return normalize_entidade(nome)


def normalize_contratante(nome):
    fundo = _normalizar_fundo_municipal_unico(nome)
    if fundo is not None:
        return fundo

    return normalize_entidade(nome)


def normalize_processo(processo):
    """Produz a identidade textual canônica de um processo administrativo."""
    if processo is None or not isinstance(processo, str):
        return None

    normalizado = processo.strip()
    normalizado = re.sub(r"\s*/\s*", "/", normalizado)
    normalizado = re.sub(r"[,.]+\s*$", "", normalizado)

    return normalizado.strip() or None


def normalize_contrato(contrato):
    """Produz a identidade textual canônica de um contrato."""
    if contrato is None or not isinstance(contrato, str):
        return None

    normalizado = contrato.strip()
    normalizado = re.sub(r"\s*([./-])\s*", r"\1", normalizado)
    normalizado = re.sub(r"[.,;:]+\s*$", "", normalizado)

    return normalizado.strip() or None
