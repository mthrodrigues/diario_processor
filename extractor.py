import pdfplumber
from dataclasses import dataclass
from ftfy import fix_text


@dataclass(frozen=True)
class LinhaPagina:
    pagina: int
    indice: int
    texto: str
    top: float
    bottom: float
    incluir_no_texto_saneado: bool = True


@dataclass(frozen=True)
class TextoPaginado:
    linhas: tuple[LinhaPagina, ...]


def extrair_texto(pdf_path):
    texto = ""

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            conteudo = pagina.extract_text()
            if conteudo:
                # 🔥 correção robusta de encoding
                conteudo = fix_text(conteudo)
                texto += conteudo + "\n"

    return texto


def extrair_texto_paginado(pdf_path):
    """Extrai linhas posicionadas preservando a ordem do texto do PDF."""
    linhas = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina_numero, pagina in enumerate(pdf.pages, start=1):
            linhas_pagina = pagina.extract_text_lines(
                return_chars=False,
            )

            for indice, linha in enumerate(linhas_pagina):
                linhas.append(
                    LinhaPagina(
                        pagina=pagina_numero,
                        indice=indice,
                        texto=fix_text(linha["text"]),
                        top=linha["top"],
                        bottom=linha["bottom"],
                    )
                )

    return TextoPaginado(tuple(linhas))