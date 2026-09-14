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
        self.assertEqual(metadados["contrato_normalizado"], "002.023.2026")
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
        self.assertIsNone(metadados["contrato_normalizado"])
        self.assertIsNone(metadados["valor_principal"])
        self.assertIsNone(metadados["vigencia"])
        self.assertIsNone(metadados["objeto"])

    def test_corrigenda_usa_fornecedor_do_leia_se(self):
        texto = (
            "CORRIGENDA DA PUBLICAÇÃO DE 02 DE FEVEREIRO DE 2026\n"
            'Onde se lê: ""Contrato n° 007.01.2022 '
            "(Prestação de serviço de gerenciamento da manutenção preventiva e "
            "corretiva de veículos leves, semi leves, pesados, semi pesados e "
            "das máquinas de terraplanagem). Contratante: O Fundo Municipal "
            "de Saúde de Teresópolis. Contratada: Prime Consultoria e "
            "Assessoria Empresarial. - Objeto: Fica prorrogado por mais "
            '12 (doze) meses.""\n'
            'Leia-se: ""Contrato n° 007.01.2022 '
            "(Prestação de serviço de gerenciamento da manutenção preventiva e "
            "corretiva de veículos leves, semi leves, pesados, semi pesados e "
            "das máquinas de terraplanagem). Contratante: O Fundo Municipal "
            "de Saúde de Teresópolis. Contratada: Hospital em Casa Produtos "
            "Médicos Ltda. - Objeto: Fica prorrogado por mais 12 (doze) "
            'meses.""'
        )

        metadados = extrair_metadados_bloco(texto)

        self.assertEqual(metadados["tipo"], "corrigenda")
        self.assertEqual(
            metadados["fornecedor"],
            "Hospital em Casa Produtos Médicos Ltda",
        )
        self.assertEqual(
            metadados["fornecedor_normalizado"],
            "HOSPITAL EM CASA PRODUTOS MEDICOS",
        )

    def test_corrigenda_com_uma_contratada_extrai_fornecedor(self):
        texto = (
            "CORRIGENDA DA PUBLICAÇÃO\n"
            "Contrato n° 021.009.2026. "
            "Contratante: O Município de Teresópolis. "
            "Contratada: Enge Prat Engenharia e Serviços Ltda. "
            "Objeto: Prestação de serviços. "
            "Onde se lê: Contrato n° 021.009.2026. "
            "Leia-se: Contrato n° 021.009.2026."
        )

        metadados = extrair_metadados_bloco(texto)

        self.assertEqual(metadados["tipo"], "corrigenda")
        self.assertEqual(
            metadados["fornecedor"],
            "Enge Prat Engenharia e Serviços Ltda",
        )
        self.assertEqual(
            metadados["fornecedor_normalizado"],
            "ENGE PRAT ENGENHARIA E SERVICOS",
        )

    def test_aviso_extrai_numero(self):
        texto = (
            "AVISO Nº 79/2026\n"
            "Objeto: Contratação de serviços."
        )

        metadados = extrair_metadados_bloco(texto)

        assert metadados["tipo"] == "aviso"
        assert metadados["numero_aviso"] == "79/2026"

    def test_aviso_sem_numero_retorna_none(self):
        texto = (
            "AVISO DE PREGÃO\n"
            "PREGÃO ELETRÔNICO Nº 90008/2026"
        )

        metadados = extrair_metadados_bloco(texto)

        assert metadados["tipo"] == "aviso"
        assert metadados["numero_aviso"] is None

    def test_aviso_ata_registro_precos_enriquece_campos_contratuais(self):
        texto = """
        AVISO Nº 1/2026
        ATA DE REGISTRO DE PREÇOS Nº 039/2025
        Processo Administrativo nº 3.556/2025.
        Modalidade: Pregão Eletrônico nº. 90043/2025.
        Objeto: REGISTRO DE PREÇOS COM A DURAÇÃO DE 12(DOZE) MESES PARA A
        REALIZAÇÃO DE LIMPEZA DE FOSSA SÉPTICA, CAIXA DE GORDURA E ESGOTO,
        VISANDO ATENDER AS NECESSIDADES DA SECRETARIA MUNICIPAL DE
        EDUCAÇÃO
        Contratado: Os preços, as quantidades, o fornecedor e as especificações
        dos materiais registrados nesta Ata, encontram-se indicados na tabela abaixo:
        SANEADORA LAGOS LTDA CNPJ: 50.886.917/0001-03
        TOTAL R$ 104.004,00
        Valor total da proposta: R$ 104.004,00
        """

        metadados = extrair_metadados_bloco(texto)

        assert metadados["tipo"] == "aviso"
        assert metadados["numero_aviso"] == "1/2026"
        assert metadados["fornecedor"] == "SANEADORA LAGOS LTDA"
        assert metadados["fornecedor_normalizado"] is not None
        assert metadados["valor_principal"] == 104004.0
        assert metadados["objeto"] is not None
        assert "REGISTRO DE PREÇOS" in metadados["objeto"]


    def test_aviso_comum_nao_recebe_enriquecimento_contratual(self):
        texto = """
        AVISO DE PREGÃO
        PREGÃO ELETRÔNICO Nº 90008/2026
        OBJETO: contratação de empresa especializada na prestação de serviços.
        """

        metadados = extrair_metadados_bloco(texto)

        assert metadados["tipo"] == "aviso"
        assert metadados["fornecedor"] is None
        assert metadados["objeto"] is None
        assert metadados["valor_principal"] is None

    def test_aviso_ata_registro_precos_com_quebra_de_linha_enriquece_fornecedor(self):
            texto = """
            AVISO Nº 32/2026
            ADESÃO EXTERNA Nº 2/2026
            da Ata de
            Registro de Preços nº 024/2025
            formalizada através do Processo Administrativo nº 12.494/2025,
            a ser fornecida pela empresa D'CASA COMERCIO DE ALIMENTOS E BEBIDAS LTDA,
            inscrita no CNPJ nº 29.268.101/0001-20.
            """

            metadados = extrair_metadados_bloco(texto)

            assert metadados["tipo"] == "aviso"
            assert metadados["fornecedor"] == "D'CASA COMERCIO DE ALIMENTOS E BEBIDAS LTDA"
            assert metadados["fornecedor_normalizado"] is not None

    def test_corrigenda_usa_fornecedor_da_empresa_no_leia_se(self):
        texto = """
        AVISO Nº 155/2026
        CORRIGENDA REFERENTE AO AVISO Nº 144/2026.

        Onde-se lê: "a ser fornecido pela empresa MOBIT - MOBILIDADE,
        ILUMINACAO E TECNOLOGIA LTDA, inscrita no CNPJ:
        16.383.848/0001-87".

        Leia-se: "a ser fornecido pela empresa SMART CITY QUATRO
        EFICIENTIZACAO ENERGETICA E VIDEOMONITORAMENTO SPE LTDA,
        inscrita no CNPJ: 66.059.177/0001-71".
        """

        metadados = extrair_metadados_bloco(texto)

        assert metadados["tipo"] == "aviso"
        assert (
            metadados["fornecedor"]
            == "SMART CITY QUATRO EFICIENTIZACAO ENERGETICA E VIDEOMONITORAMENTO SPE LTDA"
        )

if __name__ == "__main__":
    unittest.main()
