from pathlib import Path

import pdfplumber
import pytest

from extractor import (
    LinhaPagina,
    TextoPaginado,
    extrair_texto,
    extrair_texto_paginado,
)
from parser import (
    identificar_tipo,
    sanear_texto_pdf,
    sanear_texto_paginado,
    segmentar_publicacoes,
    segmentar_publicacoes_paginado,
    serializar_bloco_paginado,
    serializar_texto_paginado,
)
from pot_extractor import (
    extrair_publicacoes_pot_estruturadas,
    extrair_publicacoes_pot_pdf,
)
from pot_segmentation import ajustar_blocos_pot_estruturais


PDFS_REAIS = Path(r"C:\automacoes\diario_bot\pdfs\2026\03")
FIXTURES = Path(__file__).parent / "fixtures"


def _blocos_ajustados(pdf_path):
    texto_paginado = sanear_texto_paginado(
        extrair_texto_paginado(pdf_path)
    )
    blocos = segmentar_publicacoes_paginado(texto_paginado)

    with pdfplumber.open(pdf_path) as pdf:
        publicacoes = extrair_publicacoes_pot_estruturadas(pdf)
        blocos_ajustados = ajustar_blocos_pot_estruturais(
            blocos,
            publicacoes,
        )

    return texto_paginado, blocos_ajustados


def _serializar_blocos(blocos):
    return [
        serializar_bloco_paginado(bloco)
        for bloco in blocos
    ]


def _linhas(blocos):
    return tuple(
        linha
        for bloco in blocos
        for linha in bloco
    )


def _blocos_pot(blocos):
    return [
        bloco
        for bloco in blocos
        if identificar_tipo(bloco) == "pot"
    ]


def test_diario_3279_isola_maurineia_do_conteudo_posterior():
    texto_paginado, blocos_paginados = _blocos_ajustados(
        PDFS_REAIS / "diario_3279.pdf"
    )
    blocos = _serializar_blocos(blocos_paginados)
    blocos_pot = _blocos_pot(blocos)

    assert len(blocos_pot) == 7
    assert _linhas(blocos_paginados) == tuple(
        linha
        for linha in texto_paginado.linhas
        if linha.incluir_no_texto_saneado
    )

    maurineia = next(
        bloco
        for bloco in blocos_pot
        if "Maurineia da" in bloco
    )

    assert "(POT) DESLIGADOS" in maurineia
    assert "GERAL" not in maurineia
    assert "PROCESSO SELETIVO" not in maurineia
    assert any(
        "PROCESSO SELETIVO" in bloco
        and identificar_tipo(bloco) != "pot"
        for bloco in blocos
    )


def test_diario_3282_preserva_continuacao_e_isola_leticiane():
    texto_paginado, blocos_paginados = _blocos_ajustados(
        PDFS_REAIS / "diario_3282.pdf"
    )
    blocos = _serializar_blocos(blocos_paginados)
    blocos_pot = _blocos_pot(blocos)

    assert len(blocos_pot) == 3
    assert any("de Leite" in bloco for bloco in blocos_pot)
    assert _linhas(blocos_paginados) == tuple(
        linha
        for linha in texto_paginado.linhas
        if linha.incluir_no_texto_saneado
    )

    leticiane = next(
        bloco
        for bloco in blocos_pot
        if "Leticiane de" in bloco
    )

    assert "BENEFICIÁRIOS DO PROGRAMA OPERAÇÃO TRABALHO (POT)" in leticiane
    assert "GERAL" not in leticiane
    assert "CÂMARA DE EDUCAÇÃO INFANTIL" not in leticiane
    assert any(
        "CÂMARA DE EDUCAÇÃO INFANTIL" in bloco
        and identificar_tipo(bloco) != "pot"
        for bloco in blocos
    )


@pytest.mark.parametrize(
    "nome_pdf",
    [
        "diario_3252.pdf",
        "diario_3328.pdf",
        "diario_3352.pdf",
        "diario_3396.pdf",
        "diario_3430.pdf",
        "diario_3431.pdf",
    ],
)
def test_integracao_pot_preserva_blocos_existentes(nome_pdf):
    pdf_path = FIXTURES / nome_pdf
    texto_legacy = sanear_texto_pdf(extrair_texto(pdf_path))
    esperado = segmentar_publicacoes(texto_legacy)

    texto_paginado, blocos_paginados = _blocos_ajustados(pdf_path)

    assert serializar_texto_paginado(texto_paginado) == texto_legacy
    assert _serializar_blocos(blocos_paginados) == esperado


def test_publicacoes_pot_legadas_permanecem_compativeis():
    pdf_path = FIXTURES / "diario_3252.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        legadas = extrair_publicacoes_pot_pdf(pdf)

    with pdfplumber.open(pdf_path) as pdf:
        estruturadas = extrair_publicacoes_pot_estruturadas(pdf)

    assert legadas == [
        publicacao["registros"]
        for publicacao in estruturadas
    ]


def test_integracao_pot_nao_altera_documento_sem_pot():
    linhas = (
        LinhaPagina(1, 0, "AVISO Nº 1/2026", 10, 20),
        LinhaPagina(1, 1, "Texto administrativo.", 25, 35),
        LinhaPagina(1, 2, "PORTARIA Nº 2/2026", 40, 50),
        LinhaPagina(1, 3, "Outro texto administrativo.", 55, 65),
    )
    blocos = segmentar_publicacoes_paginado(
        TextoPaginado(linhas)
    )

    assert ajustar_blocos_pot_estruturais(
        blocos,
        [],
    ) == blocos