import hashlib
import re

from pathlib import Path
from datetime import datetime

from config import BASE_DIARIO_PATH


# =========================================================
# PDFs
# =========================================================

def listar_pdfs():

    base_path = Path(BASE_DIARIO_PATH)

    return sorted(base_path.rglob("*.pdf"))


def calcular_pdf_hash(pdf_path):
    digest = hashlib.sha256()

    with Path(pdf_path).open("rb") as arquivo:
        for trecho in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(trecho)

    return digest.hexdigest()


# =========================================================
# ID DO DIÁRIO
# =========================================================

def extrair_diario_id(pdf_path):

    nome = Path(pdf_path).stem

    return int(nome.replace("diario_", ""))


# =========================================================
# DATA DE PUBLICAÇÃO
# =========================================================

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def extrair_data_publicacao(texto):

    if not texto:
        return None

    inicio = texto[:10000]

    inicio = re.sub(r"\s+", " ", inicio)

    inicio_upper = inicio.upper()

    # =====================================================
    # PADRÃO OFICIAL DO DIÁRIO
    #
    # Ano XI - Edição 8 TERÇA, 13 DE JANEIRO DE 2026
    # =====================================================

    match = re.search(
        r"EDIÇÃO\s+\d+.*?"
        r"(SEGUNDA|TERÇA|TERCA|QUARTA|QUINTA|SEXTA|SÁBADO|SABADO|DOMINGO)"
        r",?\s+"
        r"([0-9]{1,2})\s+DE\s+"
        r"([A-ZÇÃÕÉÁÍÓÚ]+)\s+DE\s+"
        r"([0-9]{4})",
        inicio_upper,
        re.IGNORECASE
    )

    if not match:
        return None

    dia = int(match.group(2))

    mes_nome = (
        match.group(3)
        .strip()
        .lower()
    )

    # =====================================================
    # NORMALIZA ACENTOS
    # =====================================================

    mes_nome = (
        mes_nome
        .replace("Ç", "c")
        .replace("Ã", "a")
        .replace("Á", "a")
        .replace("É", "e")
        .replace("Ê", "e")
        .replace("Í", "i")
        .replace("Ó", "o")
        .replace("Ú", "u")
        .lower()
    )

    ano = int(match.group(4))

    mes = MESES.get(mes_nome)

    if not mes:
        return None

    try:

        return datetime(
            ano,
            mes,
            dia
        ).date()

    except ValueError:

        return None