#!/usr/bin/env python3

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    segmentar_publicacoes,
)

ROOT = Path(__file__).resolve().parent.parent

CORPUS = ROOT / "tests" / "corpus"

TEXTOS = CORPUS / "textos"
EXPECTED = CORPUS / "expected"


def gerar(nome):

    texto = (TEXTOS / f"{nome}.txt").read_text(
        encoding="utf-8"
    )

    blocos = segmentar_publicacoes(texto)

    resultado = {"blocos": []}

    for indice, bloco in enumerate(blocos):

        tipo = identificar_tipo(bloco)

        resultado["blocos"].append({

            "numero_bloco": indice + 1,

            "tipo": tipo,

            "processo": extrair_processo(bloco),

            "contrato": extrair_contrato(bloco),

            "contratante": extrair_contratante(bloco),

            "fornecedor": extrair_fornecedor(bloco),

            "cnpj": extrair_cnpj(bloco),

            "valores": extrair_valores(bloco),

            "valor_principal": extrair_valor_principal(bloco),

            "vigencia": extrair_vigencia(bloco),

            "objeto": extrair_objeto(bloco),
        })

    destino = EXPECTED / f"{nome}.json"

    destino.write_text(
        json.dumps(
            resultado,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(f"Arquivo gerado: {destino}")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Uso:")
        print("    py tools/gerar_expected.py nome_do_caso")
        raise SystemExit(1)

    gerar(sys.argv[1])
