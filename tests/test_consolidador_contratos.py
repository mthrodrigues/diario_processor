import tempfile
import unittest
from pathlib import Path

import database
from consolidador_contratos import consolidar_sqlite


class ConsolidadorContratosTest(unittest.TestCase):
    def setUp(self):
        self.database_path_original = database.DATABASE_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.tmpdir.name) / "test.db"
        database.criar_tabela()

    def tearDown(self):
        database.DATABASE_PATH = self.database_path_original
        self.tmpdir.cleanup()

    def _publicacao(self, bloco, contrato, normalizado, data=None):
        database.salvar_publicacao(
            diario_id=1,
            numero_bloco=bloco,
            arquivo_path=f"diario_{bloco}.pdf",
            texto_bloco="Contrato",
            tipo="contrato",
            processo=None,
            contrato=contrato,
            contratante=None,
            fornecedor=None,
            cnpj=None,
            valores=[],
            processo_normalizado=None,
            data_publicacao=data,
            contrato_normalizado=normalizado,
        )

    def _contratos(self):
        conn = database.conectar()
        rows = conn.execute(
            "SELECT contrato, contrato_normalizado, data_primeira_publicacao, "
            "data_ultima_publicacao, quantidade_publicacoes, criado_em, atualizado_em "
            "FROM contratos ORDER BY contrato_normalizado"
        ).fetchall()
        conn.close()
        return rows

    def test_cria_um_contrato_para_multiplas_publicacoes(self):
        self._publicacao(1, "008.014.2026", "008.014.2026", "2025-02-01")
        self._publicacao(2, "8.014.2026", "008.014.2026", "2025-03-01")

        conn = database.conectar()
        self.assertEqual(consolidar_sqlite(conn), 1)
        conn.close()

        contrato = self._contratos()[0]
        self.assertEqual(
            contrato[:5],
            ("008.014.2026", "008.014.2026", "2025-02-01", "2025-03-01", 2),
        )

    def test_atualiza_contrato_existente_quando_nova_publicacao_aparece(self):
        self._publicacao(1, "1/2025", "1/2025", "2025-01-01")
        conn = database.conectar()
        consolidar_sqlite(conn)
        criado = self._contratos()[0][5]

        self._publicacao(2, "1/2025", "1/2025", "2025-02-01")
        consolidar_sqlite(conn)
        atualizado = self._contratos()[0]

        self.assertEqual(atualizado[4], 2)
        self.assertEqual(atualizado[5], criado)
        self.assertNotEqual(atualizado[6], criado)
        conn.close()

    def test_e_idempotente_quando_estado_nao_mudou(self):
        self._publicacao(1, "1/2025", "1/2025", "2025-01-01")
        conn = database.conectar()
        consolidar_sqlite(conn)
        antes = self._contratos()
        consolidar_sqlite(conn)

        self.assertEqual(self._contratos(), antes)
        conn.close()

    def test_ignora_publicacoes_sem_contrato_normalizado(self):
        self._publicacao(1, "2/2025", None, "2025-01-01")
        conn = database.conectar()
        self.assertEqual(consolidar_sqlite(conn), 0)
        conn.close()
        self.assertEqual(self._contratos(), [])

    def test_contrato_sem_data_e_aceito(self):
        self._publicacao(1, "3/2025", "3/2025")
        conn = database.conectar()
        consolidar_sqlite(conn)
        conn.close()

        self.assertEqual(self._contratos()[0][2:5], (None, None, 1))


if __name__ == "__main__":
    unittest.main()
