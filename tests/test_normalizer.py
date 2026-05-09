import unittest

from normalizer import normalize_contratante, normalize_entidade, normalize_fornecedor


class NormalizerTest(unittest.TestCase):
    def test_condor_variantes_convergem(self):
        variantes = [
            "CONDOR S.A.",
            "CONDOR S.A. INDUSTRIA QUIMICA",
            "CONDOR INDUSTRIA QUIMICA",
        ]

        normalizados = {normalize_fornecedor(variante) for variante in variantes}

        self.assertEqual(normalizados, {"CONDOR"})

    def test_remove_sufixos_empresariais(self):
        self.assertEqual(normalize_fornecedor("Empresa Alfa Ltda."), "EMPRESA ALFA")
        self.assertEqual(normalize_fornecedor("Empresa Alfa EIRELI"), "EMPRESA ALFA")
        self.assertEqual(normalize_fornecedor("Empresa Alfa S/A"), "EMPRESA ALFA")
        self.assertEqual(normalize_fornecedor("Empresa Alfa ME"), "EMPRESA ALFA")
        self.assertEqual(normalize_fornecedor("Empresa Alfa EPP"), "EMPRESA ALFA")

    def test_normaliza_acentuacao_e_pontuacao(self):
        nome = "Conta Pública Soluções Assessoria Contábil Ltda."

        self.assertEqual(
            normalize_fornecedor(nome),
            "CONTA PUBLICA SOLUCOES ASSESSORIA CONTABIL",
        )

    def test_pontuacao_redundante_vira_espaco_unico(self):
        self.assertEqual(normalize_entidade("A.B.C. - Serviços / EPP"), "A B C SERVICOS")

    def test_contratante_usa_mesma_regra_deterministica(self):
        self.assertEqual(
            normalize_contratante("Município de Teresópolis"),
            "MUNICIPIO DE TERESOPOLIS",
        )

    def test_valores_vazios(self):
        self.assertIsNone(normalize_fornecedor(None))
        self.assertIsNone(normalize_fornecedor("   "))


if __name__ == "__main__":
    unittest.main()
