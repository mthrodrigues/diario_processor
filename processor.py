from classifier import classificar_relevancia, deve_enriquecer_contratual, eh_tipo_prioritario
from normalizer import normalize_contratante, normalize_fornecedor
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


def extrair_metadados_bloco(texto_bloco):
    tipo = identificar_tipo(texto_bloco)
    relevancia = classificar_relevancia(tipo)
    prioritario = eh_tipo_prioritario(tipo)

    metadados = {
        "tipo": tipo,
        "relevancia": relevancia,
        "prioritario": prioritario,
        "processo": extrair_processo(texto_bloco),
        "contrato": extrair_contrato(texto_bloco),
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

    if deve_enriquecer_contratual(tipo):
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
