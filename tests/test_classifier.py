import unittest

from classifier import (
    TIPOS_PRIORITARIOS,
    classificar_relevancia,
    deve_enriquecer_contratual,
    eh_tipo_prioritario,
)


class ClassificadorDocumentalTest(unittest.TestCase):
    def test_tipos_prioritarios_sao_contratos_e_extratos(self):
        self.assertEqual(TIPOS_PRIORITARIOS, ["contrato", "extrato"])
        self.assertTrue(eh_tipo_prioritario("contrato"))
        self.assertTrue(eh_tipo_prioritario("extrato"))
        self.assertFalse(eh_tipo_prioritario("aviso"))
        self.assertFalse(eh_tipo_prioritario("aditivo"))

    def test_relevancia_documental(self):
        self.assertEqual(classificar_relevancia("contrato"), "alta")
        self.assertEqual(classificar_relevancia("extrato"), "alta")
        self.assertEqual(classificar_relevancia("homologacao"), "media")
        self.assertEqual(classificar_relevancia("adjudicacao"), "media")
        self.assertEqual(classificar_relevancia("aviso"), "baixa")
        self.assertEqual(classificar_relevancia("desconhecido"), "baixa")

    def test_enriquecimento_contratual_fica_restrito_a_prioritarios(self):
        self.assertTrue(deve_enriquecer_contratual("contrato"))
        self.assertTrue(deve_enriquecer_contratual("extrato"))
        self.assertFalse(deve_enriquecer_contratual("homologacao"))
        self.assertFalse(deve_enriquecer_contratual("portaria"))


if __name__ == "__main__":
    unittest.main()
