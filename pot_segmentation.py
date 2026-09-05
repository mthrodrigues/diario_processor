"""Integra fronteiras físicas POT a blocos textuais com proveniência."""
import re

from parser import identificar_tipo, serializar_bloco_paginado


PADRAO_CABECALHO_POT = re.compile(
    r"BENEFICI[ÁA]RIOS\s+DO\s+PROGRAMA\s+OPERA[ÇC][ÃA]O\s+TRABALHO",
    flags=re.IGNORECASE,
)


def _contem_cabecalho_pot(texto):
    return bool(PADRAO_CABECALHO_POT.search(texto))


TOLERANCIA_VERTICAL = 1.0


def _indice_final_publicacao(bloco, publicacao):
    ultima_tabela = publicacao["tabelas"][-1]
    pagina_final = ultima_tabela["pagina"]
    _, _, _, bottom = ultima_tabela["bbox"]

    indices = [
        indice
        for indice, linha in enumerate(bloco)
        if linha.pagina < pagina_final
        or (
            linha.pagina == pagina_final
            and linha.bottom <= bottom + TOLERANCIA_VERTICAL
        )
    ]

    return indices[-1] if indices else None


def ajustar_blocos_pot_estruturais(
    blocos,
    publicacoes_pot_estruturadas,
):
    """Divide somente blocos POT que absorveram outro documento.

    A associação segue a ordem documental dos cabeçalhos POT, mas a fronteira
    vem exclusivamente da última tabela agrupada pelo extrator POT. As linhas
    do PDF são sempre preservadas; nenhuma é reconstruída por crop.
    """
    indices_pot = [
        indice
        for indice, bloco in enumerate(blocos)
        if _contem_cabecalho_pot(
            serializar_bloco_paginado(bloco)
        )
    ]

    if len(indices_pot) != len(publicacoes_pot_estruturadas):
        return blocos

    resultado = []
    publicacoes_por_indice = dict(
        zip(indices_pot, publicacoes_pot_estruturadas)
    )

    for indice, bloco in enumerate(blocos):
        publicacao = publicacoes_por_indice.get(indice)

        if (
            publicacao is None
            or identificar_tipo(serializar_bloco_paginado(bloco)) == "pot"
        ):
            resultado.append(bloco)
            continue

        indice_final = _indice_final_publicacao(
            bloco,
            publicacao,
        )

        if indice_final is None:
            resultado.append(bloco)
            continue

        resultado.append(bloco[:indice_final + 1])

        if indice_final + 1 < len(bloco):
            resultado.append(bloco[indice_final + 1:])

    return resultado