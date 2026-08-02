import unittest

from processor import extrair_metadados_bloco


class ProcessorBlocoTest(unittest.TestCase):
    def test_contrato_recebe_enriquecimento_contratual(self):
        texto = (
            "Contrato n° 002.023.2026\n"
            "Contratante: O Município de Teresópolis. Contratada: Condor S.A. Indústria Química.\n"
            "Objeto: Aquisição de equipamento. Valor R$: 41.985,00. Prazo: 180 dias.\n"
            "Processo n° 1.387/2026."
        )

        metadados = extrair_metadados_bloco(texto)

        self.assertEqual(metadados["tipo"], "contrato")
        self.assertEqual(metadados["processo_normalizado"], "1.387/2026")
        self.assertEqual(metadados["fornecedor"], "Condor S.A. Indústria Química")
        self.assertEqual(metadados["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(metadados["contratante"], "O Município de Teresópolis")
        self.assertEqual(metadados["contratante_normalizado"], "O MUNICIPIO DE TERESOPOLIS")
        self.assertEqual(metadados["valor_principal"], 41985.0)
        self.assertEqual(metadados["vigencia"], "180 dias")
        self.assertEqual(metadados["objeto"], "Aquisição de equipamento")

    def test_aviso_preserva_basico_sem_enriquecimento_contratual(self):
        texto = (
            "AVISO Nº 79/2026\n"
            "Objeto: Contratação de serviços. Leia-se: proposta final apresenta valor de R$ 5.541,00."
        )

        metadados = extrair_metadados_bloco(texto)

        self.assertEqual(metadados["tipo"], "aviso")
        self.assertEqual(metadados["valores"], [5541.0])
        self.assertIsNone(metadados["fornecedor"])
        self.assertIsNone(metadados["fornecedor_normalizado"])
        self.assertIsNone(metadados["contratante"])
        self.assertIsNone(metadados["contratante_normalizado"])
        self.assertIsNone(metadados["processo_normalizado"])
        self.assertIsNone(metadados["valor_principal"])
        self.assertIsNone(metadados["vigencia"])
        self.assertIsNone(metadados["objeto"])


if __name__ == "__main__":
    unittest.main()
