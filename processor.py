from classifier import deve_enriquecer_contratual

from normalizer import (
    normalize_contratante,
    normalize_contrato,
    normalize_fornecedor,
    normalize_processo,
)

from parser import (
    extrair_cnpj,
    extrair_contratante,
    extrair_contrato,
    extrair_fornecedor,
    extrair_objeto,
    extrair_processo,
    extrair_valor_principal,
    extrair_valores,
    extrair_vigencia,
    identificar_tipo,
)


def _termo_tem_estrutura_contratual(texto_bloco):
    texto_upper = texto_bloco.upper()

    pos_contratante = texto_upper.find("CONTRATANTE:")
    pos_contratada = texto_upper.find("CONTRATADA:")
    pos_objeto = texto_upper.find("OBJETO:")

    return (
        pos_contratante >= 0
        and pos_contratada >= 0
        and pos_objeto >= 0
        and pos_contratante < pos_objeto
        and pos_contratada < pos_objeto
    )


def extrair_metadados_bloco(texto_bloco):
    tipo = identificar_tipo(texto_bloco)
    metadados = {
        "tipo": tipo,
        "processo": extrair_processo(texto_bloco),
        "processo_normalizado": None,
        "contrato": extrair_contrato(texto_bloco),
        "contrato_normalizado": None,
        "cnpj": extrair_cnpj(texto_bloco),
        "valores": extrair_valores(texto_bloco),
        "contratante": None,
        "contratante_normalizado": None,
        "fornecedor": None,
        "fornecedor_normalizado": None,
        "valor_principal": None,
        "vigencia": None,
        "objeto": None,
    }

    metadados["processo_normalizado"] = normalize_processo(metadados["processo"])
    metadados["contrato_normalizado"] = normalize_contrato(metadados["contrato"])

    enriquecer_contratual = deve_enriquecer_contratual(tipo)

    if tipo == "termo" and _termo_tem_estrutura_contratual(texto_bloco):
        enriquecer_contratual = True

    if enriquecer_contratual:
        contratante = extrair_contratante(texto_bloco)
        fornecedor = extrair_fornecedor(texto_bloco)

        metadados.update(
            {
                "contratante": contratante,
                "contratante_normalizado": normalize_contratante(contratante),
                "fornecedor": fornecedor,
                "fornecedor_normalizado": normalize_fornecedor(fornecedor),
                "valor_principal": extrair_valor_principal(texto_bloco),
                "vigencia": extrair_vigencia(texto_bloco),
                "objeto": extrair_objeto(texto_bloco),
            }
        )

    return metadados
