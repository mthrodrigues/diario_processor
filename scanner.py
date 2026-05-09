from pathlib import Path
from config import BASE_DIARIO_PATH


def listar_pdfs():
    pdfs = list(BASE_DIARIO_PATH.rglob("diario_*.pdf"))
    return pdfs


def extrair_diario_id(caminho_pdf: Path):
    nome = caminho_pdf.stem
    return int(nome.split("_")[1])