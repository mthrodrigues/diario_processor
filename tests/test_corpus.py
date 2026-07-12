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

TEXTOS_DIR = CORPUS_DIR / "textos"
EXPECTED_DIR = CORPUS_DIR / "expected"


class CorpusParserTest(unittest.TestCase):

    def test_corpus(self):

        arquivos = sorted(TEXTOS_DIR.glob("*.txt"))

        self.assertGreater(
            len(arquivos),
            0,
            "Nenhum caso encontrado no corpus."
        )

        for arquivo in arquivos:

            nome = arquivo.stem

            expected_file = EXPECTED_DIR / f"{nome}.json"

            self.assertTrue(
                expected_file.exists(),
                f"Arquivo esperado inexistente: {expected_file.name}"
            )

            texto = arquivo.read_text(
                encoding="utf-8"
            )

            esperado = json.loads(
                expected_file.read_text(
                    encoding="utf-8"
                )
            )

            blocos = segmentar_publicacoes(texto)

            self.assertEqual(
                len(blocos),
                len(esperado["blocos"]),
                f"{nome}: quantidade de blocos diferente"
            )

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

                self.assertEqual(
                    observado,
                    esperado_bloco,
                    f"{nome} - bloco {indice + 1}"
                )


if __name__ == "__main__":
    unittest.main()