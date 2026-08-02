import unittest

from classifier import deve_enriquecer_contratual


class ClassificadorDocumentalTest(unittest.TestCase):
    def test_enriquecimento_contratual_fica_restrito_a_tipos_contratuais(self):
        self.assertTrue(deve_enriquecer_contratual("contrato"))
        self.assertTrue(deve_enriquecer_contratual("extrato"))
        self.assertFalse(deve_enriquecer_contratual("homologacao"))
        self.assertFalse(deve_enriquecer_contratual("portaria"))


if __name__ == "__main__":
    unittest.main()
