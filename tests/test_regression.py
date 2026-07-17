from pathlib import Path

from extractor import extrair_texto
from parser import identificar_tipo, segmentar_publicacoes


PDF = Path(
    r"C:\automacoes\diario_bot\pdfs\2026\02\diario_3265.pdf"
)


def carregar_diario() -> str:
    """Extrai o texto completo do Diário Oficial."""

    assert PDF.exists(), f"PDF não encontrado: {PDF}"

    return extrair_texto(str(PDF))


def extrair_publicacao(texto: str, inicio: str, fim: str) -> str:
    """
    Extrai uma publicação específica do diário.
    """

    pos_inicio = texto.find(inicio)
    assert pos_inicio != -1, f"Texto inicial não encontrado: {inicio}"

    pos_fim = texto.find(fim, pos_inicio)
    assert pos_fim != -1, f"Texto final não encontrado: {fim}"

    return texto[pos_inicio:pos_fim]


def test_portaria_gp_311():

    texto = carregar_diario()

    publicacao = extrair_publicacao(
        texto,
        "PORTARIA GP Nº 311, DE 25 DE FEVEREIRO DE 2026.",
        "PORTARIA GP Nº 312, DE 25 DE FEVEREIRO DE 2026.",
    )

    blocos = segmentar_publicacoes(publicacao)

    #
    # A publicação inteira deve permanecer em um único bloco.
    #
    assert len(blocos) == 1

    bloco = blocos[0]

    #
    # Deve continuar sendo identificada como Portaria.
    #
    assert identificar_tipo(bloco) == "portaria"

    #
    # O parser NÃO pode quebrar a publicação quando encontra
    # o cabeçalho da tabela.
    #
    assert "Contrato nº:" in bloco
    assert "Contratado(a):" in bloco
    assert "Objeto:" in bloco
    assert "Art. 2º" in bloco
    assert "Art. 3º" in bloco

    #
    # Deve conter o encerramento da publicação.
    #
    assert "= Prefeito =" in bloco