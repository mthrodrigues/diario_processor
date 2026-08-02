import unittest

from parser import (
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


class ParserDocumentalTest(unittest.TestCase):
    def test_fornecedor_para_antes_de_objeto(self):
        texto = (
            "Contrato n° 002.023.2026\n"
            "Contratante: O Município de Teresópolis através da Secretaria Municipal de Segurança,\n"
            "Ordem Pública e Mobilidade. Contratada: Condor S.A. Indústria Química. - Objeto:\n"
            "Aquisição de item. Valor R$: 41.985,00. Processo n° 1.387/2026."
        )

        self.assertEqual(extrair_fornecedor(texto), "Condor S.A. Indústria Química")
        self.assertEqual(
            extrair_contratante(texto),
            "O Município de Teresópolis através da Secretaria Municipal de Segurança, Ordem Pública e Mobilidade",
        )
        self.assertEqual(extrair_valores(texto), [41985.0])
        self.assertEqual(extrair_valor_principal(texto), 41985.0)
        self.assertEqual(extrair_vigencia(texto), None)
        self.assertEqual(extrair_objeto(texto), "Aquisição de item")

    def test_termo_extrai_permissionario_e_numero_do_instrumento(self):
        texto = (
            "Termo de Permissão de Uso a Título Precário n° 031.001.2026\n"
            "Permitente: O Município de Teresópolis através da Secretaria Municipal de Governo e\n"
            "Coordenação. Permissionário: Iracema Regina da Silva. - Objeto: Permitir uso.\n"
            "Processo n° 13.935/2025."
        )

        self.assertEqual(extrair_contrato(texto), "031.001.2026")
        self.assertEqual(extrair_processo(texto), "13.935/2025")
        self.assertEqual(extrair_fornecedor(texto), "Iracema Regina da Silva")

    def test_processo_nao_confunde_numero_de_aviso(self):
        texto = (
            "AVISO Nº 79/2026\n"
            "ERRATA REFERENTE AO EXTRATO DO TERMO DE HOMOLOGAÇÃO E\n"
            "ADJUDICAÇÃO\n"
            "OBJETO: Contratação de serviços."
        )

        self.assertEqual(identificar_tipo(texto), "aviso")
        self.assertIsNone(extrair_processo(texto))

    def test_valor_principal_prefere_leia_se_em_errata(self):
        texto = (
            "Onde se lê: proposta final apresenta valor de R$ 5.927,67.\n"
            "Leia-se: proposta final apresenta valor de R$ 5.541,00."
        )

        self.assertEqual(extrair_valores(texto), [5927.67, 5541.0])
        self.assertEqual(extrair_valor_principal(texto), 5541.0)

    def test_segmentacao_nao_quebra_titulo_multilinha(self):
        texto = (
            "AVISO Nº 79/2026\n"
            "ERRATA REFERENTE AO EXTRATO DO TERMO DE HOMOLOGAÇÃO E\n"
            "ADJUDICAÇÃO\n"
            "OBJETO: Contratação de serviços.\n"
            "BENEFICIÁRIOS DO PROGRAMA OPERAÇÃO TRABALHO DESLIGADOS\n"
            "Nome Data\n"
        )

        blocos = segmentar_publicacoes(texto)

        self.assertEqual(len(blocos), 2)
        self.assertTrue(blocos[0].startswith("AVISO Nº 79/2026"))
        self.assertTrue(blocos[1].startswith("BENEFICIÁRIOS DO PROGRAMA"))

    def test_extrato_contratual_com_vigencia_e_objeto(self):
        texto = (
            "EXTRATO DE CONTRATO Nº 014/2026\n"
            "Contratante: Fundo Municipal de Saúde. Contratada: Empresa Alfa Serviços Ltda.\n"
            "Objeto: Prestação de serviços de manutenção preventiva dos equipamentos.\n"
            "Valor total R$ 120.000,00. Vigência: 12 (doze) meses. Processo nº 1.234/2026."
        )

        self.assertEqual(identificar_tipo(texto), "extrato")
        self.assertEqual(extrair_contrato(texto), "014/2026")
        self.assertEqual(extrair_fornecedor(texto), "Empresa Alfa Serviços Ltda")
        self.assertEqual(extrair_contratante(texto), "Fundo Municipal de Saúde")
        self.assertEqual(extrair_valor_principal(texto), 120000.0)
        self.assertEqual(extrair_vigencia(texto), "12 (doze) meses")
        self.assertEqual(
            extrair_objeto(texto),
            "Prestação de serviços de manutenção preventiva dos equipamentos",
        )

    def test_aditivo_e_identificado_como_aditivo(self):
        texto = (
            "TERMO ADITIVO Nº 02 AO CONTRATO Nº 010/2025\n"
            "Contratada: Empresa Beta Ltda. Objeto: Prorrogação de prazo."
        )

        self.assertEqual(identificar_tipo(texto), "aditivo")
        self.assertEqual(extrair_fornecedor(texto), "Empresa Beta Ltda")


if __name__ == "__main__":
    unittest.main()
