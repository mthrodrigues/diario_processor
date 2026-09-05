import sys
import types
import unittest

from config import PostgresConfig, get_postgres_config
from infra.db.connection import PostgresConnectionPool
from infra.db.migrations.runner import quote_ident, run_migrations
from infra.db.repositories.publicacao_repository import PublicacaoRepository
from infra.db.repositories.pot_repository import PotRepository
from consolidador_contratos import consolidar_postgres as consolidar_contratos_postgres


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))

    def fetchall(self):
        if self.conn.fetchall_queue:
            return self.conn.fetchall_queue.pop(0)

        return []

    def fetchone(self):
        if self.conn.fetchone_queue:
            return self.conn.fetchone_queue.pop(0)

        return None


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.fetchall_queue = []
        self.fetchone_queue = []

    def cursor(self):
        return FakeCursor(self)


class PostgresInfraTest(unittest.TestCase):
    def test_config_carrega_postgres_do_env(self):
        config = get_postgres_config()

        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.db, "inteligencia_cidada")
        self.assertEqual(config.user, "postgres")
        self.assertEqual(config.schema, "diario")

    def test_quote_ident_rejeita_identificador_invalido(self):
        self.assertEqual(quote_ident("diario"), '"diario"')

        with self.assertRaises(ValueError):
            quote_ident("diario;drop")

    def test_connection_pool_usa_timeout_e_pool_simples(self):
        chamadas = {}

        class DummyPool:
            def __init__(self, minconn, maxconn, **kwargs):
                chamadas["minconn"] = minconn
                chamadas["maxconn"] = maxconn
                chamadas["kwargs"] = kwargs

        modulo_psycopg2 = types.ModuleType("psycopg2")
        modulo_pool = types.ModuleType("psycopg2.pool")
        modulo_pool.SimpleConnectionPool = DummyPool

        original_psycopg2 = sys.modules.get("psycopg2")
        original_pool = sys.modules.get("psycopg2.pool")
        sys.modules["psycopg2"] = modulo_psycopg2
        sys.modules["psycopg2.pool"] = modulo_pool

        try:
            config = PostgresConfig(
                host="localhost",
                port=5432,
                db="inteligencia_cidada",
                user="postgres",
                password="postgres123",
                schema="diario",
                connect_timeout=7,
                retry_attempts=1,
                retry_delay_seconds=0,
                min_pool_size=1,
                max_pool_size=3,
            )
            pool = PostgresConnectionPool(config)._criar_pool()
        finally:
            if original_psycopg2 is None:
                sys.modules.pop("psycopg2", None)
            else:
                sys.modules["psycopg2"] = original_psycopg2

            if original_pool is None:
                sys.modules.pop("psycopg2.pool", None)
            else:
                sys.modules["psycopg2.pool"] = original_pool

        self.assertIsInstance(pool, DummyPool)
        self.assertEqual(chamadas["minconn"], 1)
        self.assertEqual(chamadas["maxconn"], 3)
        self.assertEqual(chamadas["kwargs"]["connect_timeout"], 7)
        self.assertEqual(chamadas["kwargs"]["dbname"], "inteligencia_cidada")

    def test_run_migrations_usa_schema_diario_e_registra_versao(self):
        conn = FakeConnection()
        conn.fetchall_queue.append([])

        run_migrations(conn, schema="diario")

        sql_executado = "\n".join(sql for sql, _params in conn.executed)

        self.assertIn('CREATE SCHEMA IF NOT EXISTS "diario"', sql_executado)
        self.assertIn('"diario".schema_migrations', sql_executado)
        self.assertIn('"diario".publicacoes', sql_executado)
        self.assertIn("idx_diario_publicacoes_fornecedor_normalizado", sql_executado)
        self.assertIn("idx_diario_publicacoes_processo_normalizado", sql_executado)
        self.assertIn("idx_diario_publicacoes_contrato_normalizado", sql_executado)

    def test_run_migrations_cria_contratos_e_indice(self):
        conn = FakeConnection()
        conn.fetchall_queue.append([])

        run_migrations(conn, schema="diario")

        sql_executado = "\n".join(sql for sql, _params in conn.executed)

        self.assertIn('"diario".contratos', sql_executado)
        self.assertIn("idx_diario_contratos_contrato_normalizado", sql_executado)

    def test_run_migrations_adiciona_pdf_hash_e_constraint_de_unicidade(self):
        conn = FakeConnection()
        conn.fetchall_queue.append([])

        run_migrations(conn, schema="diario")

        sql_executado = "\n".join(sql for sql, _params in conn.executed)

        self.assertIn(
            'ALTER TABLE "diario".publicacoes\nADD COLUMN IF NOT EXISTS pdf_hash TEXT;',
            sql_executado,
        )
        self.assertIn(
            'ALTER TABLE "diario".publicacoes\nADD COLUMN IF NOT EXISTS parser_version TEXT;',
            sql_executado,
        )
        self.assertIn("ADD CONSTRAINT uq_publicacoes_pdf_bloco", sql_executado)
        self.assertIn("UNIQUE (pdf_hash, numero_bloco)", sql_executado)
        self.assertIn("possui definicao incompativel", sql_executado)

    def test_consolidador_contratos_usa_sql_e_parametros_postgres(self):
        conn = FakeConnection()
        conn.fetchall_queue.append([
            ("001/2026", "001/2026", "2026-01-01", "2026-02-01", 2)
        ])

        self.assertEqual(consolidar_contratos_postgres(conn, schema="diario"), 1)

        sql, params = conn.executed[-1]
        self.assertIn('"diario".contratos', sql)
        self.assertIn('ON CONFLICT (contrato_normalizado)', sql)
        self.assertEqual(params[:5], ("001/2026", "001/2026", "2026-01-01", "2026-02-01", 2))

    def test_repository_salvar_publicacao_usa_schema_dedicado(self):
        conn = FakeConnection()
        conn.fetchone_queue.append((123,))
        repo = PublicacaoRepository(conn, schema="diario")

        publicacao_id = repo.salvar_publicacao(
            diario_id=1,
            numero_bloco=1,
            arquivo_path="diario_1.pdf",
            texto_bloco="RAW",
            tipo="contrato",
            processo="1/2026",
            contrato="001/2026",
            contratante="Municipio",
            fornecedor="Condor",
            cnpj=None,
            valores=[100.0],
            valor_principal=100.0,
            vigencia="12 meses",
            objeto="Objeto",
            fornecedor_normalizado="CONDOR",
            contratante_normalizado="MUNICIPIO",
            processo_normalizado="1/2026",
            data_publicacao="2026-07-30",
            contrato_normalizado="001/2026",
        )

        sql, params = conn.executed[-1]

        self.assertIn('"diario".publicacoes', sql)
        self.assertIn("%s::jsonb", sql)
        self.assertEqual(params[0], 1)
        self.assertEqual(params[2], "diario_1.pdf")
        self.assertEqual(params[7], "001/2026")
        self.assertEqual(params[13], "[100.0]")
        self.assertEqual(params[-4], "1/2026")
        self.assertEqual(params[-3], "2026-07-30")
        self.assertIsNone(params[-2])
        self.assertIsNone(params[-1])
        self.assertIn("data_publicacao", sql)
        self.assertIn("pdf_hash", sql)
        self.assertIn("ON CONFLICT (pdf_hash, numero_bloco)", sql)
        self.assertIn("RETURNING id", sql)
        self.assertEqual(publicacao_id, 123)

    def test_repository_salvar_publicacao_recalcula_contratante_normalizado(self):
        conn = FakeConnection()
        conn.fetchone_queue.append((123,))
        repo = PublicacaoRepository(conn, schema="diario")

        repo.salvar_publicacao(
            diario_id=1,
            numero_bloco=1,
            arquivo_path="diario_1.pdf",
            texto_bloco="RAW",
            tipo="contrato",
            processo="1/2026",
            contrato="001/2026",
            contratante="O Município de Teresópolis através da Secretaria Municipal de Educação",
            fornecedor="Condor",
            cnpj=None,
            valores=[100.0],
            valor_principal=100.0,
            vigencia="12 meses",
            objeto="Objeto",
            fornecedor_normalizado="CONDOR",
            contratante_normalizado="MUNICIPIO ANTIGO",
            processo_normalizado="1/2026",
            data_publicacao="2026-07-30",
            contrato_normalizado="001/2026",
        )

        sql, params = conn.executed[-1]
        self.assertEqual(params[11], "O MUNICIPIO DE TERESOPOLIS ATRAVES DA SECRETARIA MUNICIPAL DE EDUCACAO")

    def test_repository_ja_processado(self):
        conn = FakeConnection()
        conn.fetchone_queue.append((1,))
        repo = PublicacaoRepository(conn, schema="diario")

        self.assertTrue(repo.ja_processado("diario_1.pdf"))
        self.assertIn('"diario".publicacoes', conn.executed[-1][0])

    def test_repository_listar_fornecedores_consolidados(self):
        conn = FakeConnection()
        conn.fetchall_queue.append([
            ("CONDOR", 2, 300.0, ["Condor S.A.", "Condor Industria Quimica"])
        ])
        repo = PublicacaoRepository(conn, schema="diario")

        resultado = repo.listar_fornecedores_consolidados()

        self.assertEqual(resultado[0]["fornecedor_normalizado"], "CONDOR")
        self.assertEqual(resultado[0]["ocorrencias"], 2)
        self.assertEqual(resultado[0]["valor_total"], 300.0)

    def test_repository_pot_salva_registros(self):
        conn = FakeConnection()
        repo = PotRepository(conn, schema="diario")

        registros = [
            {
                "numero": "1",
                "beneficiario": "Maria da Silva",
                "unidade": "EM Exemplo",
                "horario_atuacao": None,
                "area_aprendizado": "Apoio/Escolar",
                "data_inclusao": "05/02/2026",
                "data_desligamento": None,
                "substituicao": "Joana da Silva",
                "texto_bruto": "1 Maria da Silva EM Exemplo",
            },
            {
                "numero": "2",
                "beneficiario": "João dos Santos",
                "unidade": "EM Teste",
                "horario_atuacao": "07:00h às 13:00h",
                "area_aprendizado": "APOIO/ESCOLAR",
                "data_inclusao": None,
                "data_desligamento": "21/08/2026",
                "substituicao": None,
                "texto_bruto": "2 João dos Santos EM Teste",
            },
        ]

        quantidade = repo.salvar_registros(
            publicacao_id=123,
            registros=registros,
        )

        self.assertEqual(quantidade, 2)
        self.assertEqual(len(conn.executed), 2)

        sql_1, params_1 = conn.executed[0]
        sql_2, params_2 = conn.executed[1]

        self.assertIn('"diario".pot_beneficiarios', sql_1)
        self.assertIn('"diario".pot_beneficiarios', sql_2)

        self.assertEqual(params_1[0], 123)
        self.assertEqual(params_1[1], "1")
        self.assertEqual(params_1[2], "Maria da Silva")
        self.assertEqual(params_1[3], "EM Exemplo")
        self.assertIsNone(params_1[4])
        self.assertEqual(params_1[5], "Apoio/Escolar")
        self.assertEqual(params_1[6], "2026-02-05")
        self.assertIsNone(params_1[7])
        self.assertEqual(params_1[8], "Joana da Silva")

        self.assertEqual(params_2[0], 123)
        self.assertEqual(params_2[1], "2")
        self.assertEqual(params_2[2], "João dos Santos")
        self.assertEqual(params_2[4], "07:00h às 13:00h")
        self.assertEqual(params_2[5], "APOIO/ESCOLAR")
        self.assertIsNone(params_2[6])
        self.assertEqual(params_2[7], "2026-08-21")
        self.assertIsNone(params_2[8])

    def test_repository_pot_nao_executa_sem_registros(self):
        conn = FakeConnection()
        repo = PotRepository(conn, schema="diario")

        quantidade = repo.salvar_registros(
            publicacao_id=123,
            registros=[],
        )

        self.assertEqual(quantidade, 0)
        self.assertEqual(conn.executed, [])

    def test_repository_pot_substitui_registros(self):
        conn = FakeConnection()
        repo = PotRepository(conn, schema="diario")

        registros = [
            {
                "numero": "1",
                "beneficiario": "Maria da Silva",
                "unidade": "EM Exemplo",
                "horario_atuacao": None,
                "area_aprendizado": "Apoio/Escolar",
                "data_inclusao": "05/02/2026",
                "data_desligamento": None,
                "substituicao": "Joana da Silva",
                "texto_bruto": "1 Maria da Silva EM Exemplo",
            },
            {
                "numero": "2",
                "beneficiario": "João dos Santos",
                "unidade": "EM Teste",
                "horario_atuacao": "07:00h às 13:00h",
                "area_aprendizado": "Apoio/Escolar",
                "data_inclusao": None,
                "data_desligamento": "21/08/2026",
                "substituicao": None,
                "texto_bruto": "2 João dos Santos EM Teste",
            },
        ]

        quantidade = repo.substituir_registros(
            publicacao_id=123,
            registros=registros,
        )

        self.assertEqual(quantidade, 2)
        self.assertEqual(len(conn.executed), 3)

        sql_delete, params_delete = conn.executed[0]

        self.assertIn(
            'DELETE FROM "diario".pot_beneficiarios',
            sql_delete,
        )
        self.assertEqual(
            params_delete,
            (123,),
        )

        sql_insert_1, params_1 = conn.executed[1]
        sql_insert_2, params_2 = conn.executed[2]

        self.assertIn(
            '"diario".pot_beneficiarios',
            sql_insert_1,
        )
        self.assertIn(
            '"diario".pot_beneficiarios',
            sql_insert_2,
        )

        self.assertEqual(params_1[0], 123)
        self.assertEqual(params_1[1], "1")
        self.assertEqual(params_1[2], "Maria da Silva")
        self.assertEqual(params_1[6], "2026-02-05")

        self.assertEqual(params_2[0], 123)
        self.assertEqual(params_2[1], "2")
        self.assertEqual(params_2[2], "João dos Santos")
        self.assertEqual(params_2[7], "2026-08-21")

    def test_repository_pot_substitui_registros_por_lista_vazia(self):
        conn = FakeConnection()
        repo = PotRepository(conn, schema="diario")

        quantidade = repo.substituir_registros(
            publicacao_id=123,
            registros=[],
        )

        self.assertEqual(quantidade, 0)
        self.assertEqual(len(conn.executed), 1)

        sql, params = conn.executed[0]

        self.assertIn(
            'DELETE FROM "diario".pot_beneficiarios',
            sql,
        )
        self.assertEqual(params, (123,))

if __name__ == "__main__":
    unittest.main()
