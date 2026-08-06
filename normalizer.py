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


def normalize_fornecedor(nome):
    return normalize_entidade(nome)


def normalize_contratante(nome):
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
