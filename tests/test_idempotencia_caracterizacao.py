from contextlib import contextmanager
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

import main
from infra.db.repositories.publicacao_repository import PublicacaoRepository


PUBLICACAO = {
    "diario_id": 3279,
    "numero_bloco": 7,
    "arquivo_path": "C:/pdfs/diario_3279.pdf",
    "texto_bloco": "Texto bruto do bloco.",
    "tipo": "pot",
    "processo": None,
    "contrato": None,
    "contratante": None,
    "fornecedor": None,
    "cnpj": None,
    "valores": [],
    "valor_principal": None,
    "vigencia": None,
    "objeto": None,
    "fornecedor_normalizado": None,
    "contratante_normalizado": None,
    "processo_normalizado": None,
    "data_publicacao": None,
    "contrato_normalizado": None,
}


class CursorSemUnicidade:
    def __init__(self, conn):
        self.conn = conn
        self.resultado = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))

        if "INSERT INTO" in sql and "publicacoes" in sql:
            registro_id = self.conn.proximo_id
            self.conn.proximo_id += 1
            self.conn.publicacoes.append(
                {
                    "id": registro_id,
                    "arquivo_path": params[2],
                    "numero_bloco": params[1],
                }
            )
            self.resultado = (registro_id,)
            return

        if "FROM \"diario\".publicacoes" in sql and "arquivo_path" in sql:
            arquivo_path = params[0]
            self.resultado = next(
                (
                    (publicacao["id"],)
                    for publicacao in self.conn.publicacoes
                    if publicacao["arquivo_path"] == arquivo_path
                ),
                None,
            )

    def fetchone(self):
        return self.resultado


class ConexaoSemUnicidade:
    """Dublê do estado atual: INSERTs em publicacoes não têm chave única."""

    def __init__(self):
        self.executed = []
        self.publicacoes = []
        self.proximo_id = 1

    def cursor(self):
        return CursorSemUnicidade(self)


class ConexaoTransacional:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class IdempotenciaCaracterizacaoTest(TestCase):
    def test_segunda_gravacao_do_mesmo_documento_bloco_cria_dois_registros(self):
        conn = ConexaoSemUnicidade()
        repository = PublicacaoRepository(conn, schema="diario")

        primeiro_id = repository.salvar_publicacao(**PUBLICACAO)
        segundo_id = repository.salvar_publicacao(**PUBLICACAO)

        self.assertNotEqual(primeiro_id, segundo_id)
        self.assertEqual(len(conn.publicacoes), 2)
        self.assertEqual(
            [
                (publicacao["arquivo_path"], publicacao["numero_bloco"])
                for publicacao in conn.publicacoes
            ],
            [
                (PUBLICACAO["arquivo_path"], PUBLICACAO["numero_bloco"]),
                (PUBLICACAO["arquivo_path"], PUBLICACAO["numero_bloco"]),
            ],
        )
        self.assertTrue(
            all("ON CONFLICT (pdf_hash, numero_bloco)" in sql for sql, _ in conn.executed)
        )

    def test_ja_processado_identifica_arquivo_ja_gravado(self):
        conn = ConexaoSemUnicidade()
        repository = PublicacaoRepository(conn, schema="diario")
        repository.salvar_publicacao(**PUBLICACAO)

        self.assertTrue(repository.ja_processado(PUBLICACAO["arquivo_path"]))

    def test_ja_processado_nao_e_garantia_contra_intercalacao_concorrente(self):
        conn = ConexaoSemUnicidade()
        primeira_tentativa = PublicacaoRepository(conn, schema="diario")
        segunda_tentativa = PublicacaoRepository(conn, schema="diario")

        self.assertFalse(primeira_tentativa.ja_processado(PUBLICACAO["arquivo_path"]))
        self.assertFalse(segunda_tentativa.ja_processado(PUBLICACAO["arquivo_path"]))

        primeiro_id = primeira_tentativa.salvar_publicacao(**PUBLICACAO)
        segundo_id = segunda_tentativa.salvar_publicacao(**PUBLICACAO)

        self.assertNotEqual(primeiro_id, segundo_id)
        self.assertEqual(len(conn.publicacoes), 2)

    def test_reprocessar_tudo_bypassa_ja_processado(self):
        conn = ConexaoTransacional()
        repository = Mock()

        with self._main_isolado(conn, repository):
            with patch.object(main, "listar_pdfs", return_value=[Path("diario_3279.pdf")]), patch.object(
                main,
                "extrair_diario_id",
                return_value=3279,
            ), patch.object(
                main,
                "extrair_texto_paginado",
                side_effect=RuntimeError("falha controlada"),
            ):
                main.run()

        repository.ja_processado.assert_not_called()

    def test_falha_no_pdf_provoca_rollback_da_transacao_atual(self):
        conn = ConexaoTransacional()
        repository = Mock()

        with self._main_isolado(conn, repository):
            with patch.object(main, "listar_pdfs", return_value=[Path("diario_3279.pdf")]), patch.object(
                main,
                "extrair_diario_id",
                return_value=3279,
            ), patch.object(
                main,
                "extrair_texto_paginado",
                side_effect=RuntimeError("falha controlada"),
            ):
                main.run()

        self.assertEqual(conn.rollbacks, 1)

    def test_keyboard_interrupt_provoca_rollback_da_transacao_atual(self):
        conn = ConexaoTransacional()
        repository = Mock()

        with self._main_isolado(conn, repository):
            with patch.object(main, "listar_pdfs", return_value=[Path("diario_3279.pdf")]), patch.object(
                main,
                "extrair_diario_id",
                return_value=3279,
            ), patch.object(
                main,
                "calcular_pdf_hash",
                side_effect=KeyboardInterrupt,
            ):
                main.run()

        self.assertEqual(conn.rollbacks, 1)

    @contextmanager
    def _main_isolado(self, conn, repository):
        @contextmanager
        def postgres_connection_falsa():
            yield conn

        with patch.object(main, "postgres_connection", postgres_connection_falsa), patch.object(
            main,
            "PublicacaoRepository",
            return_value=repository,
        ), patch.object(main, "PotRepository"), patch.object(
            main,
            "EventoRepository",
        ), patch.object(main, "EntityRepository"), patch.object(
            main,
            "EntityRelationshipRepository",
        ), patch.object(main, "TimelineRepository"), patch.object(
            main,
            "InstitutionalEventOutboxRepository",
        ), patch.object(main, "setup_logging", return_value=Mock()), patch.object(
            main,
            "novo_run_id",
            return_value="teste",
        ), patch.object(main, "log_erro"), patch.object(
            main,
            "log_sucesso",
        ), patch.object(main, "consolidar_postgres"), patch.object(
            main,
            "consolidar_contratos_postgres",
        ):
            yield