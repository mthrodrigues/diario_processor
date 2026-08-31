from pathlib import Path

import pdfplumber

from extractor import extrair_texto
from parser import segmentar_publicacoes, identificar_tipo
from pot_extractor import extrair_publicacoes_pot_pdf


FIXTURES = (
    Path(__file__).parent / "fixtures"
)


def test_fixtures_pot_correspondem_aos_blocos_segmentados():
    casos = [
        ("diario_3252.pdf", 4, [104, 6, 6, 14]),
        ("diario_3352.pdf", 1, [1]),
        ("diario_3431.pdf", 1, [5]),
    ]

    for nome_pdf, quantidade_blocos, tamanhos_esperados in casos:
        pdf_path = FIXTURES / nome_pdf

        texto = extrair_texto(str(pdf_path))
        blocos = segmentar_publicacoes(texto)

        blocos_pot = [
            bloco
            for bloco in blocos
            if identificar_tipo(bloco) == "pot"
        ]

        with pdfplumber.open(pdf_path) as pdf:
            publicacoes_pot = extrair_publicacoes_pot_pdf(pdf)

        assert len(blocos_pot) == quantidade_blocos, nome_pdf
        assert len(publicacoes_pot) == quantidade_blocos, nome_pdf

        assert [
            len(publicacao)
            for publicacao in publicacoes_pot
        ] == tamanhos_esperados, nome_pdf