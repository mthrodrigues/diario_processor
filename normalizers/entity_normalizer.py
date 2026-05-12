import re
import unicodedata


# =========================================================
# ABREVIAÇÕES
# =========================================================

ABREVIACOES = {

    "SEC ": "SECRETARIA ",
    "SEC. ": "SECRETARIA ",
    "MUN ": "MUNICIPAL ",
    "MUN. ": "MUNICIPAL ",
    "ADM ": "ADMINISTRACAO ",
    "ADM. ": "ADMINISTRACAO ",

}


# =========================================================
# TERMOS IRRELEVANTES
# =========================================================

TERMOS_IRRELEVANTES = {

    "DA",
    "DE",
    "DO",
    "DOS",
    "DAS",

}


# =========================================================
# PREFIXOS ADMINISTRATIVOS
# =========================================================

PADROES_RUIDO = [

    r"^\s*A\s+SERVIDORA\s+",
    r"^\s*O\s+SERVIDOR\s+",

    r"^\s*A\s+SENHORA\s+",
    r"^\s*O\s+SENHOR\s+",

    r"^\s*SR[A]?\s+",
    r"^\s*DR[A]?\s+",

]


# =========================================================
# ACENTOS
# =========================================================

def remover_acentos(texto):

    return "".join(

        c for c in unicodedata.normalize("NFD", texto)

        if unicodedata.category(c) != "Mn"
    )


# =========================================================
# NORMALIZAÇÃO PRINCIPAL
# =========================================================

def normalize_entity_name(nome):

    if not nome:
        return None

    # =====================================================
    # NORMALIZA BASE
    # =====================================================

    nome = nome.strip()

    nome = remover_acentos(nome)

    nome = nome.upper()

    # =====================================================
    # REMOVE PREFIXOS DE RUÍDO
    # =====================================================

    for padrao in PADROES_RUIDO:

        nome = re.sub(
            padrao,
            "",
            nome,
            flags=re.IGNORECASE
        )

    # =====================================================
    # EXPANDE ABREVIAÇÕES
    # =====================================================

    for abreviado, completo in ABREVIACOES.items():

        nome = nome.replace(abreviado, completo)

    # =====================================================
    # REMOVE PONTUAÇÃO
    # =====================================================

    nome = re.sub(r"[^A-Z0-9\s]", " ", nome)

    # =====================================================
    # REMOVE ESPAÇOS DUPLOS
    # =====================================================

    nome = re.sub(r"\s+", " ", nome)

    nome = nome.strip()

    # =====================================================
    # REMOVE TERMOS IRRELEVANTES
    # =====================================================

    partes = []

    for parte in nome.split():

        if parte in TERMOS_IRRELEVANTES:
            continue

        partes.append(parte)

    nome = " ".join(partes)

    return nome or None