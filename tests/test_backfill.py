import tempfile
import unittest
from pathlib import Path

import analytics
import backfill
import database


CONTRATO_TEXTO = (
    "Contrato n° 002.023.2026\n"
    "Contratante: O Município de Teresópolis. Contratada: Condor S.A. Indústria Química.\n"
    "Objeto: Aquisição de equipamento. Valor R$: 41.985,00. Prazo: 180 dias.\n"
    "Processo n° 1.387/2026."
)


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.database_path_original = database.DATABASE_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.tmpdir.name) / "backfill.db"
        database.criar_tabela()

    def tearDown(self):
        database.DATABASE_PATH = self.database_path_original
        self.tmpdir.cleanup()

    def _inserir_publicacao_antiga(self, **campos):
        dados = {
            "diario_id": 1,
            "numero_bloco": 1,
            "arquivo_path": "diario_antigo.pdf",
            "texto_bloco": CONTRATO_TEXTO,
            "tipo": "contrato",
            "processo": None,
            "contrato": None,
            "contratante": None,
            "fornecedor": None,
            "cnpj": None,
            "valores": "[]",
            "data_processamento": "2026-05-08T10:00:00",
        }
        dados.update(campos)

        colunas = ", ".join(dados.keys())
        placeholders = ", ".join("?" for _ in dados)
        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO publicacoes ({colunas}) VALUES ({placeholders})",
            list(dados.values()),
        )
        conn.commit()
        registro_id = cursor.lastrowid
        conn.close()

        return registro_id

    def _buscar(self, registro_id):
        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM publicacoes WHERE id = ?", (registro_id,))
        linha = cursor.fetchone()
        colunas = [descricao[0] for descricao in cursor.description]
        conn.close()

        return dict(zip(colunas, linha))

    def test_preenche_campos_vazios_sem_reprocessar_pdf(self):
        registro_id = self._inserir_publicacao_antiga(
            fornecedor="Condor S.A. Indústria Química",
            contratante="O Município de Teresópolis",
        )

        resumo = backfill.executar_backfill()
        registro = self._buscar(registro_id)

        self.assertEqual(resumo.analisados, 1)
        self.assertEqual(resumo.atualizados, 1)
        self.assertEqual(registro["texto_bloco"], CONTRATO_TEXTO)
        self.assertEqual(registro["fornecedor"], "Condor S.A. Indústria Química")
        self.assertEqual(registro["contratante"], "O Município de Teresópolis")
        self.assertEqual(registro["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(registro["contratante_normalizado"], "O MUNICIPIO DE TERESOPOLIS")
        self.assertEqual(registro["processo"], "1.387/2026")
        self.assertEqual(registro["contrato"], "002.023.2026")
        self.assertEqual(registro["valor_principal"], 41985.0)
        self.assertEqual(registro["vigencia"], "180 dias")
        self.assertEqual(registro["objeto"], "Aquisição de equipamento")
        self.assertEqual(registro["relevancia"], "alta")
        self.assertEqual(registro["prioritario"], 1)

    def test_nao_sobrescreve_dados_validos(self):
        registro_id = self._inserir_publicacao_antiga(
            fornecedor="Fornecedor Manual",
            fornecedor_normalizado="FORNECEDOR MANUAL",
            contratante="Contratante Manual",
            contratante_normalizado="CONTRATANTE MANUAL",
            valor_principal=999.0,
            objeto="Objeto revisado manualmente",
        )

        backfill.executar_backfill()
        registro = self._buscar(registro_id)

        self.assertEqual(registro["fornecedor"], "Fornecedor Manual")
        self.assertEqual(registro["fornecedor_normalizado"], "FORNECEDOR MANUAL")
        self.assertEqual(registro["contratante"], "Contratante Manual")
        self.assertEqual(registro["contratante_normalizado"], "CONTRATANTE MANUAL")
        self.assertEqual(registro["valor_principal"], 999.0)
        self.assertEqual(registro["objeto"], "Objeto revisado manualmente")
        self.assertEqual(registro["texto_bloco"], CONTRATO_TEXTO)

    def test_only_normalization_nao_preenche_campos_analiticos(self):
        registro_id = self._inserir_publicacao_antiga(
            fornecedor="Condor S.A. Indústria Química",
            contratante="O Município de Teresópolis",
        )

        backfill.executar_backfill(only_normalization=True)
        registro = self._buscar(registro_id)

        self.assertEqual(registro["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(registro["contratante_normalizado"], "O MUNICIPIO DE TERESOPOLIS")
        self.assertIsNone(registro["valor_principal"])
        self.assertIsNone(registro["relevancia"])
        self.assertIsNone(registro["objeto"])

    def test_only_analytics_fields_nao_preenche_normalizacao(self):
        registro_id = self._inserir_publicacao_antiga(
            fornecedor="Condor S.A. Indústria Química",
            contratante="O Município de Teresópolis",
        )

        backfill.executar_backfill(only_analytics_fields=True)
        registro = self._buscar(registro_id)

        self.assertIsNone(registro["fornecedor_normalizado"])
        self.assertIsNone(registro["contratante_normalizado"])
        self.assertEqual(registro["valor_principal"], 41985.0)
        self.assertEqual(registro["relevancia"], "alta")

    def test_limit_restringe_quantidade_analisada(self):
        primeiro = self._inserir_publicacao_antiga(numero_bloco=1, arquivo_path="diario_1.pdf")
        segundo = self._inserir_publicacao_antiga(numero_bloco=2, arquivo_path="diario_2.pdf")

        resumo = backfill.executar_backfill(limit=1)

        self.assertEqual(resumo.analisados, 1)
        self.assertIsNotNone(self._buscar(primeiro)["valor_principal"])
        self.assertIsNone(self._buscar(segundo)["valor_principal"])

    def test_backfill_mantem_consistencia_analitica(self):
        self._inserir_publicacao_antiga(
            fornecedor="Condor S.A. Indústria Química",
            contratante="O Município de Teresópolis",
        )

        backfill.executar_backfill()
        recorrentes = analytics.fornecedores_mais_recorrentes()

        self.assertEqual(recorrentes[0]["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(recorrentes[0]["ocorrencias"], 1)
        self.assertEqual(recorrentes[0]["valor_total"], 41985.0)


if __name__ == "__main__":
    unittest.main()
