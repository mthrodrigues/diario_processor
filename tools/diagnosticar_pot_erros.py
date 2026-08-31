from pathlib import Path
import subprocess
import sys
import textwrap

PDFS = {
    3216: r"C:\automacoes\diario_bot\pdfs\2026\01\diario_3216.pdf",
    3246: r"C:\automacoes\diario_bot\pdfs\2026\02\diario_3246.pdf",
    3279: r"C:\automacoes\diario_bot\pdfs\2026\03\diario_3279.pdf",
    3295: r"C:\automacoes\diario_bot\pdfs\2026\03\diario_3295.pdf",
    3330: r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3330.pdf",
    3344: r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3344.pdf",
    3350: r"C:\automacoes\diario_bot\pdfs\2026\05\diario_3350.pdf",
    3354: r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3354.pdf",
    3367: r"C:\automacoes\diario_bot\pdfs\2026\06\diario_3367.pdf",
    3389: r"C:\automacoes\diario_bot\pdfs\2026\07\diario_3389.pdf",
    3396: r"C:\automacoes\diario_bot\pdfs\2026\07\diario_3396.pdf",
    3418: r"C:\automacoes\diario_bot\pdfs\2026\08\diario_3418.pdf",
    3430: r"C:\automacoes\diario_bot\pdfs\2026\08\diario_3430.pdf",
}

codigo = r'''
from pathlib import Path
import pdfplumber

from extractor import extrair_texto
from parser import segmentar_publicacoes, identificar_tipo
from pot_extractor import extrair_publicacoes_pot_pdf

pdf_path = Path(sys.argv[1])

print("PDF:", pdf_path)

try:
    texto = extrair_texto(pdf_path)
    print("ETAPA TEXTO: OK")
    print("TAMANHO TEXTO:", len(texto or ""))

    blocos = segmentar_publicacoes(texto)
    print("ETAPA SEGMENTAÇÃO: OK")
    print("TOTAL BLOCOS:", len(blocos))

    blocos_pot = [
        (i, bloco)
        for i, bloco in enumerate(blocos, start=1)
        if identificar_tipo(bloco) == "pot"
    ]

    print("BLOCOS POT:", len(blocos_pot))
    print(
        "BLOCOS POT NÚMEROS:",
        [i for i, _ in blocos_pot],
    )

except Exception as exc:
    print("ETAPA TEXTO/SEGMENTAÇÃO: ERRO")
    print(type(exc).__name__ + ":", exc)
    raise

try:
    with pdfplumber.open(pdf_path) as pdf:
        publicacoes_pot = extrair_publicacoes_pot_pdf(pdf)

    print("ETAPA EXTRAÇÃO POT: OK")
    print("PUBLICAÇÕES POT:", len(publicacoes_pot))
    print(
        "TAMANHOS:",
        [len(publicacao) for publicacao in publicacoes_pot],
    )

    if len(blocos_pot) != len(publicacoes_pot):
        print(
            "DIVERGÊNCIA:",
            len(blocos_pot),
            "blocos POT vs",
            len(publicacoes_pot),
            "publicações POT",
        )
    else:
        print("CARDINALIDADE POT: OK")

except Exception as exc:
    print("ETAPA EXTRAÇÃO POT: ERRO")
    print(type(exc).__name__ + ":", exc)
    raise
'''

print("=" * 90)
print("DIAGNÓSTICO DOS 13 DIÁRIOS COM ERRO")
print("=" * 90)

for diario_id, pdf_path in PDFS.items():
    print()
    print("#" * 90)
    print("DIÁRIO:", diario_id)
    print("#" * 90)

    comando = [
        sys.executable,
        "-c",
        "import sys\n" + codigo,
        pdf_path,
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )

        print(resultado.stdout)

        if resultado.returncode == 0:
            print("RESULTADO FINAL: OK")
        else:
            print("RESULTADO FINAL: ERRO")
            print("STDERR:")
            print(resultado.stderr)

    except subprocess.TimeoutExpired:
        print(
            "RESULTADO FINAL: TIMEOUT (> 90 segundos)"
        )

print()
print("=" * 90)
print("FIM DO DIAGNÓSTICO")
print("=" * 90)
