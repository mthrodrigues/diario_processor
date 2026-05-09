import json
import unittest
from pathlib import Path

from classifier import classificar_relevancia, eh_tipo_prioritario
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


CORPUS_DIR = Path(__file__).parent / "corpus"


class CorpusParserTest(unittest.TestCase):
    def test_extrato_contrato_anonimizado(self):
        texto = (CORPUS_DIR / "textos" / "extrato_contrato_anon.txt").read_text(encoding="utf-8")
        esperado = json.loads(
            (CORPUS_DIR / "expected" / "extrato_contrato_anon.json").read_text(encoding="utf-8")
        )

        blocos = segmentar_publicacoes(texto)

        self.assertEqual(len(blocos), len(esperado["blocos"]))

        for indice, bloco in enumerate(blocos):
            esperado_bloco = esperado["blocos"][indice]
            tipo = identificar_tipo(bloco)

            observado = {
                "numero_bloco": indice + 1,
                "tipo": tipo,
                "relevancia": classificar_relevancia(tipo),
                "prioritario": eh_tipo_prioritario(tipo),
                "processo": extrair_processo(bloco),
                "contrato": extrair_contrato(bloco),
                "contratante": extrair_contratante(bloco),
                "fornecedor": extrair_fornecedor(bloco),
                "cnpj": extrair_cnpj(bloco),
                "valores": extrair_valores(bloco),
                "valor_principal": extrair_valor_principal(bloco),
                "vigencia": extrair_vigencia(bloco),
                "objeto": extrair_objeto(bloco),
            }

            self.assertEqual(observado, esperado_bloco)


if __name__ == "__main__":
    unittest.main()
