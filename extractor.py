import pdfplumber
from ftfy import fix_text


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