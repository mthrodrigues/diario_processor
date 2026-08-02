import tempfile
import unittest
from pathlib import Path

import analytics
import database


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.database_path_original = database.DATABASE_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.tmpdir.name) / "analytics.db"
        database.criar_tabela()
        self._popular_base()

    def tearDown(self):
        database.DATABASE_PATH = self.database_path_original
        self.tmpdir.cleanup()

    def _salvar(
        self,
        numero_bloco,
        tipo,
        fornecedor,
        fornecedor_normalizado,
        contratante,
        contratante_normalizado,
        valor_principal,
        contrato=None,
        objeto=None,
    ):
        database.salvar_publicacao(
            diario_id=3304,
            numero_bloco=numero_bloco,
            arquivo_path=f"diario_3304_{numero_bloco}.pdf",
            texto_bloco=f"RAW bloco {numero_bloco}",
            tipo=tipo,
            processo=f"{numero_bloco}/2026",
            contrato=contrato or f"00{numero_bloco}/2026",
            contratante=contratante,
            fornecedor=fornecedor,
            cnpj=None,
            valores=[valor_principal] if valor_principal is not None else [],
            valor_principal=valor_principal,
            vigencia=None,
            objeto=objeto,
            fornecedor_normalizado=fornecedor_normalizado,
            contratante_normalizado=contratante_normalizado,
        )

    def _popular_base(self):
        self._salvar(
            1,
            "contrato",
            "Condor S.A. Indústria Química",
            "CONDOR",
            "Secretaria Municipal de Segurança",
            "SECRETARIA MUNICIPAL DE SEGURANCA",
            100.0,
            "001/2026",
            "Aquisição de equipamento",
        )
        self._salvar(
            2,
            "extrato",
            "CONDOR INDUSTRIA QUIMICA",
            "CONDOR",
            "Secretaria Municipal de Segurança",
            "SECRETARIA MUNICIPAL DE SEGURANCA",
            200.0,
            "002/2026",
            "Aquisição complementar",
        )
        self._salvar(
            3,
            "contrato",
            "Empresa Alfa Ltda",
            "EMPRESA ALFA",
            "Fundo Municipal de Saúde",
            "FUNDO MUNICIPAL DE SAUDE",
            500.0,
            "003/2026",
            "Prestação de serviços",
        )
        self._salvar(
            4,
            "aviso",
            "Empresa Ruido Ltda",
            "EMPRESA RUIDO",
            "Secretaria Administrativa",
            "SECRETARIA ADMINISTRATIVA",
            9999.0,
            "004/2026",
            "Aviso sem contrato estruturado",
        )

        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE publicacoes SET data_processamento = ? WHERE numero_bloco IN (1, 2)",
            ("2026-05-08T10:00:00",),
        )
        cursor.execute(
            "UPDATE publicacoes SET data_processamento = ? WHERE numero_bloco = 3",
            ("2026-04-15T10:00:00",),
        )
        cursor.execute(
            "UPDATE publicacoes SET data_processamento = ? WHERE numero_bloco = 4",
            ("2026-05-09T10:00:00",),
        )
        conn.commit()
        conn.close()

    def test_fornecedores_mais_recorrentes_agrega_orgaos_e_valores(self):
        resultados = analytics.fornecedores_mais_recorrentes(limite=5)

        self.assertEqual(resultados[0]["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(resultados[0]["ocorrencias"], 2)
        self.assertEqual(resultados[0]["valor_total"], 300.0)
        self.assertEqual(
            resultados[0]["orgaos_relacionados"],
            ["SECRETARIA MUNICIPAL DE SEGURANCA"],
        )
        self.assertCountEqual(
            resultados[0]["fornecedores_originais"],
            ["Condor S.A. Indústria Química", "CONDOR INDUSTRIA QUIMICA"],
        )

    def test_orgaos_que_mais_contratam(self):
        resultados = analytics.orgaos_que_mais_contratam(limite=5)

        self.assertEqual(resultados[0]["contratante_normalizado"], "SECRETARIA MUNICIPAL DE SEGURANCA")
        self.assertEqual(resultados[0]["quantidade_contratos"], 2)
        self.assertEqual(resultados[0]["valor_total"], 300.0)

    def test_maiores_contratos_ordena_por_valor(self):
        resultados = analytics.maiores_contratos(limite=2)

        self.assertEqual(resultados[0]["contrato"], "003/2026")
        self.assertEqual(resultados[0]["fornecedor"], "Empresa Alfa Ltda")
        self.assertEqual(resultados[0]["valor_principal"], 500.0)
        self.assertEqual(resultados[1]["contrato"], "002/2026")

    def test_contratos_por_periodo_com_filtros(self):
        resultados = analytics.contratos_por_periodo(ano=2026, mes=5)

        self.assertEqual(
            resultados,
            [
                {
                    "ano": "2026",
                    "mes": "05",
                    "quantidade_contratos": 2,
                    "valor_total": 300.0,
                }
            ],
        )

    def test_analise_nao_remove_raw(self):
        analytics.fornecedores_mais_recorrentes()

        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT texto_bloco FROM publicacoes WHERE numero_bloco = 1")
        texto_bloco = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(texto_bloco, "RAW bloco 1")


if __name__ == "__main__":
    unittest.main()
