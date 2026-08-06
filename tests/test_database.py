import tempfile
import unittest
from pathlib import Path

import database


class DatabaseNormalizacaoTest(unittest.TestCase):
    def setUp(self):
        self.database_path_original = database.DATABASE_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.tmpdir.name) / "test.db"
        database.criar_tabela()

    def tearDown(self):
        database.DATABASE_PATH = self.database_path_original
        self.tmpdir.cleanup()

    def test_persiste_normalizados_sem_sobrescrever_raw(self):
        database.salvar_publicacao(
            diario_id=1,
            numero_bloco=1,
            arquivo_path="diario_1.pdf",
            texto_bloco="Contrato",
            tipo="contrato",
            processo="1/2026",
            contrato="001/2026",
            contratante="Município de Teresópolis",
            fornecedor="Condor S.A. Indústria Química",
            cnpj=None,
            valores=[100.0],
            valor_principal=100.0,
            vigencia="12 meses",
            objeto="Aquisição",
            fornecedor_normalizado="CONDOR",
            contratante_normalizado="MUNICIPIO DE TERESOPOLIS",
            processo_normalizado="1/2026",
            data_publicacao="2026-07-30",
            contrato_normalizado="001/2026",
        )

        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT fornecedor, fornecedor_normalizado, contratante, contratante_normalizado,
                   processo_normalizado, data_publicacao
                   , contrato_normalizado
            FROM publicacoes
            """
        )
        resultado = cursor.fetchone()
        conn.close()

        self.assertEqual(
            resultado,
            (
                "Condor S.A. Indústria Química",
                "CONDOR",
                "Município de Teresópolis",
                "MUNICIPIO DE TERESOPOLIS",
                "1/2026",
                "2026-07-30",
                "001/2026",
            ),
        )

    def test_criar_tabela_mantem_data_publicacao_em_schema_existente(self):
        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(publicacoes)")
        colunas = {linha[1] for linha in cursor.fetchall()}
        conn.close()

        self.assertIn("data_publicacao", colunas)

    def test_listar_fornecedores_consolidados(self):
        for indice, fornecedor in enumerate(
            ["CONDOR S.A.", "CONDOR S.A. INDUSTRIA QUIMICA", "CONDOR INDUSTRIA QUIMICA"],
            start=1,
        ):
            database.salvar_publicacao(
                diario_id=1,
                numero_bloco=indice,
                arquivo_path=f"diario_{indice}.pdf",
                texto_bloco="Contrato",
                tipo="contrato",
                processo=f"{indice}/2026",
                contrato=f"00{indice}/2026",
                contratante="Município",
                fornecedor=fornecedor,
                cnpj=None,
                valores=[100.0 * indice],
                valor_principal=100.0 * indice,
                vigencia=None,
                objeto=None,
                fornecedor_normalizado="CONDOR",
                contratante_normalizado="MUNICIPIO",
            )

        consolidados = database.listar_fornecedores_consolidados()

        self.assertEqual(consolidados[0]["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(consolidados[0]["ocorrencias"], 3)
        self.assertEqual(consolidados[0]["valor_total"], 600.0)
        self.assertCountEqual(
            consolidados[0]["fornecedores_originais"],
            ["CONDOR S.A.", "CONDOR S.A. INDUSTRIA QUIMICA", "CONDOR INDUSTRIA QUIMICA"],
        )

    def test_indices_analiticos_sao_criados(self):
        conn = database.conectar()
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(publicacoes)")
        indices = {linha[1] for linha in cursor.fetchall()}
        conn.close()

        self.assertIn("idx_publicacoes_fornecedor_normalizado", indices)
        self.assertIn("idx_publicacoes_contratante_normalizado", indices)
        self.assertIn("idx_publicacoes_processo_normalizado", indices)
        self.assertIn("idx_publicacoes_contrato_normalizado", indices)
        self.assertIn("idx_publicacoes_valor_principal", indices)
        self.assertIn("idx_publicacoes_tipo", indices)


if __name__ == "__main__":
    unittest.main()
