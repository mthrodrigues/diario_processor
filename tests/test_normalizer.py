import unittest

from normalizer import (
    normalize_contratante,
    normalize_contrato,
    normalize_entidade,
    normalize_fornecedor,
    normalize_processo,
)


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

    def test_fundo_municipal_positivo(self):
        casos = [
            ("O Fundo Municipal de Saúde", "FUNDO MUNICIPAL SAUDE"),
            ("O Fundo Municipal de Saúde de Teresópolis", "FUNDO MUNICIPAL SAUDE"),
            ("O Município de Teresópolis através do Fundo Municipal de Saúde", "FUNDO MUNICIPAL SAUDE"),
            ("O Município de Teresópolis através do Fundo Municipal de Saúde de Teresópolis", "FUNDO MUNICIPAL SAUDE"),
            ("O Fundo Municipal de Assistência Social", "FUNDO MUNICIPAL ASSISTENCIA SOCIAL"),
            ("O Município de Teresópolis através do Fundo Municipal de Assistência Social", "FUNDO MUNICIPAL ASSISTENCIA SOCIAL"),
            ("O Fundo Municipal de Segurança Pública", "FUNDO MUNICIPAL SEGURANCA PUBLICA"),
            ("O Fundo Municipal dos Direitos da Criança e do Adolescente de Teresópolis", "FUNDO MUNICIPAL DOS DIREITOS DA CRIANCA E DO ADOLESCENTE"),
            ("O Fundo Municipal de Assistência Social e Direitos Humanos", "FUNDO MUNICIPAL ASSISTENCIA SOCIAL E DIREITOS HUMANOS"),
        ]

        for valor, esperado in casos:
            with self.subTest(valor=valor):
                self.assertEqual(normalize_contratante(valor), esperado)

    def test_fundo_municipal_negativo(self):
        casos = [
            "O Fundo Municipal de Saúde e Mitra Diocesana de Petrópolis",
            "O Fundo Municipal de Saúde e os Srs",
            "O Fundo Municipal de Solidariedade do Município de Teresópolis",
            "O Município de Teresópolis através da Secretaria Municipal de Educação",
            "O Município de Teresópolis através da Secretaria Municipal de Assistência Social e Direitos Humanos e do Fundo Municipal de Saúde",
            "Secretaria Municipal de Assistência Social e Direitos Humanos",
            "O Fundo Municipal dos Direitos da Criança e do Adolescente e o Fundo Municipal de Assistência Social",
            "O Fundo Municipal de Assistência Social e o Fundo Municipal dos Direitos da Criança e do Adolescente de Teresópolis",
            "O Município de Teresópolis através da Secretaria Municipal de Administração, O Fundo Municipal de Saúde e o Fundo Municipal de Assistência Social e Direitos Humanos",
        ]

        for valor in casos:
            with self.subTest(valor=valor):
                self.assertEqual(normalize_contratante(valor), normalize_entidade(valor))

    def test_normaliza_processo_sem_alterar_identidade(self):
        self.assertIsNone(normalize_processo(None))
        self.assertIsNone(normalize_processo(""))
        self.assertEqual(normalize_processo(" 8.575 /2025, "), "8.575/2025")
        self.assertEqual(normalize_processo("214.400-6/2025"), "214.400-6/2025")
        self.assertEqual(normalize_processo("214.400-6/2025."), "214.400-6/2025")
        self.assertEqual(
            normalize_processo("63386.000421/2025-30"),
            "63386.000421/2025-30",
        )
        self.assertEqual(
            normalize_processo("04105.0000001409/2024"),
            "04105.0000001409/2024",
        )
        self.assertEqual(normalize_processo("52/26"), "52/26")

    def test_normaliza_contrato_sem_alterar_identidade(self):
        self.assertIsNone(normalize_contrato(None))
        self.assertIsNone(normalize_contrato(""))
        self.assertIsNone(normalize_contrato("   "))
        self.assertEqual(normalize_contrato(" 002 . 023 / 2026, "), "002.023/2026")
        self.assertEqual(normalize_contrato("002.023.2026."), "002.023.2026")
        self.assertEqual(normalize_contrato("002.023.2026;"), "002.023.2026")
        self.assertEqual(normalize_contrato("002.023.2026"), "002.023.2026")
        self.assertEqual(normalize_contrato("000.014.2026"), "000.014.2026")


if __name__ == "__main__":
    unittest.main()
