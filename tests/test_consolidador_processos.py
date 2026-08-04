import tempfile
import unittest
from pathlib import Path

import database
from consolidador_processos import consolidar_sqlite


class ConsolidadorProcessosTest(unittest.TestCase):
    def setUp(self):
        self.database_path_original = database.DATABASE_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.tmpdir.name) / "test.db"
        database.criar_tabela()

    def tearDown(self):
        database.DATABASE_PATH = self.database_path_original
        self.tmpdir.cleanup()

    def _publicacao(self, bloco, processo, normalizado, data=None):
        database.salvar_publicacao(
            diario_id=1,
            numero_bloco=bloco,
            arquivo_path=f"diario_{bloco}.pdf",
            texto_bloco="Processo",
            tipo="processo",
            processo=processo,
            contrato=None,
            contratante=None,
            fornecedor=None,
            cnpj=None,
            valores=[],
            processo_normalizado=normalizado,
            data_publicacao=data,
        )

    def _processos(self):
        conn = database.conectar()
        rows = conn.execute(
            "SELECT processo, processo_normalizado, data_primeira_publicacao, "
            "data_ultima_publicacao, quantidade_publicacoes, criado_em, atualizado_em "
            "FROM processos ORDER BY processo_normalizado"
        ).fetchall()
        conn.close()
        return rows

    def test_cria_um_processo_para_multiplas_publicacoes(self):
        self._publicacao(1, "8.575/2025", "8.575/2025", "2025-02-01")
        self._publicacao(2, "008.575/2025", "8.575/2025", "2025-03-01")

        conn = database.conectar()
        self.assertEqual(consolidar_sqlite(conn), 1)
        conn.close()
        processo = self._processos()[0]

        self.assertEqual(processo[:5], ("008.575/2025", "8.575/2025", "2025-02-01", "2025-03-01", 2))

    def test_atualiza_processo_existente_quando_nova_publicacao_aparece(self):
        self._publicacao(1, "1/2025", "1/2025", "2025-01-01")
        conn = database.conectar()
        consolidar_sqlite(conn)
        criado = self._processos()[0][5]

        self._publicacao(2, "1/2025", "1/2025", "2025-02-01")
        consolidar_sqlite(conn)
        atualizado = self._processos()[0]

        self.assertEqual(atualizado[4], 2)
        self.assertEqual(atualizado[5], criado)
        self.assertNotEqual(atualizado[6], criado)
        conn.close()

    def test_e_idempotente_quando_estado_nao_mudou(self):
        self._publicacao(1, "1/2025", "1/2025", "2025-01-01")
        conn = database.conectar()
        consolidar_sqlite(conn)
        antes = self._processos()
        consolidar_sqlite(conn)

        self.assertEqual(self._processos(), antes)
        conn.close()

    def test_processo_sem_data_e_aceito(self):
        self._publicacao(1, "2/2025", "2/2025")
        conn = database.conectar()
        consolidar_sqlite(conn)
        conn.close()

        self.assertEqual(self._processos()[0][2:5], (None, None, 1))

    def test_ignora_publicacoes_sem_processo_normalizado(self):
        self._publicacao(1, "3/2025", None, "2025-01-01")
        conn = database.conectar()
        self.assertEqual(consolidar_sqlite(conn), 0)
        conn.close()
        self.assertEqual(self._processos(), [])


if __name__ == "__main__":
    unittest.main()
