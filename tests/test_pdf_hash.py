import hashlib
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import main
from scanner import calcular_pdf_hash


METADADOS = {
    "tipo": "aviso",
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
    "contrato_normalizado": None,
}


class ConexaoTransacional:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class PdfHashTest(TestCase):
    def test_mesmos_bytes_produzem_o_mesmo_hash(self):
        with tempfile.TemporaryDirectory() as diretorio:
            primeiro = Path(diretorio) / "primeiro.pdf"
            segundo = Path(diretorio) / "segundo.pdf"
            primeiro.write_bytes(b"%PDF-1.4\nconteudo")
            segundo.write_bytes(b"%PDF-1.4\nconteudo")

            self.assertEqual(calcular_pdf_hash(primeiro), calcular_pdf_hash(segundo))

    def test_bytes_diferentes_produzem_hashes_diferentes(self):
        with tempfile.TemporaryDirectory() as diretorio:
            primeiro = Path(diretorio) / "primeiro.pdf"
            segundo = Path(diretorio) / "segundo.pdf"
            primeiro.write_bytes(b"%PDF-1.4\nconteudo A")
            segundo.write_bytes(b"%PDF-1.4\nconteudo B")

            self.assertNotEqual(calcular_pdf_hash(primeiro), calcular_pdf_hash(segundo))

    def test_todos_os_blocos_recebem_o_mesmo_hash_calculado_uma_vez(self):
        conn = ConexaoTransacional()
        repository = Mock()
        pdf = Path("diario_3279.pdf")
        pdf_hash = hashlib.sha256(b"diario 3279").hexdigest()

        with self._main_isolado(conn, repository), patch.object(
            main,
            "listar_pdfs",
            return_value=[pdf],
        ), patch.object(main, "extrair_diario_id", return_value=3279), patch.object(
            main,
            "calcular_pdf_hash",
            return_value=pdf_hash,
        ) as calcular_hash, patch.object(
            main,
            "extrair_texto_paginado",
            return_value=["pagina"],
        ), patch.object(main, "sanear_texto_paginado", side_effect=lambda texto: texto), patch.object(
            main,
            "serializar_texto_paginado",
            return_value="texto",
        ), patch.object(
            main,
            "extrair_data_publicacao",
            return_value=None,
        ), patch.object(
            main,
            "segmentar_publicacoes_paginado",
            return_value=["bloco 1", "bloco 2"],
        ), patch.object(
            main,
            "serializar_bloco_paginado",
            side_effect=lambda bloco: bloco,
        ), patch.object(
            main,
            "extrair_publicacoes_pot_estruturadas",
            return_value=[],
        ), patch.object(
            main,
            "ajustar_blocos_pot_estruturais",
            side_effect=lambda blocos, _pot: blocos,
        ), patch.object(main, "extrair_metadados_bloco", return_value=METADADOS), patch.object(
            main,
            "extrair_eventos_bloco",
            return_value=[],
        ):
            main.run()

        calcular_hash.assert_called_once_with(pdf)
        self.assertEqual(repository.salvar_publicacao.call_count, 2)
        self.assertEqual(
            [chamada.kwargs["pdf_hash"] for chamada in repository.salvar_publicacao.call_args_list],
            [pdf_hash, pdf_hash],
        )
        self.assertEqual(
            [chamada.args[1] for chamada in repository.salvar_publicacao.call_args_list],
            [1, 2],
        )

    def test_erro_ao_ler_pdf_para_hash_preserva_rollback_do_pdf(self):
        conn = ConexaoTransacional()
        repository = Mock()

        with self._main_isolado(conn, repository), patch.object(
            main,
            "listar_pdfs",
            return_value=[Path("diario_3279.pdf")],
        ), patch.object(main, "extrair_diario_id", return_value=3279), patch.object(
            main,
            "calcular_pdf_hash",
            side_effect=OSError("arquivo indisponivel"),
        ):
            main.run()

        self.assertEqual(conn.rollbacks, 1)
        repository.salvar_publicacao.assert_not_called()

    def test_publicacao_e_persistida_antes_dos_eventos_numerados(self):
        conn = ConexaoTransacional()
        publicacao_repository = Mock()
        publicacao_repository.salvar_publicacao.return_value = 100
        eventos = [
            {"tipo_evento": "NOMEACAO", "agente": {}, "evidencia": {}},
            {"tipo_evento": "EXONERACAO", "agente": {}, "evidencia": {}},
        ]
        ordem = []

        with self._main_isolado(conn, publicacao_repository) as evento_repository, patch.object(
            main,
            "listar_pdfs",
            return_value=[Path("diario_3279.pdf")],
        ), patch.object(main, "extrair_diario_id", return_value=3279), patch.object(
            main,
            "calcular_pdf_hash",
            return_value="a" * 64,
        ), patch.object(
            main,
            "extrair_texto_paginado",
            return_value=["pagina"],
        ), patch.object(main, "sanear_texto_paginado", side_effect=lambda texto: texto), patch.object(
            main,
            "serializar_texto_paginado",
            return_value="texto",
        ), patch.object(main, "extrair_data_publicacao", return_value=None), patch.object(
            main,
            "segmentar_publicacoes_paginado",
            return_value=["bloco"],
        ), patch.object(main, "serializar_bloco_paginado", side_effect=lambda bloco: bloco), patch.object(
            main,
            "extrair_publicacoes_pot_estruturadas",
            return_value=[],
        ), patch.object(
            main,
            "ajustar_blocos_pot_estruturais",
            side_effect=lambda blocos, _pot: blocos,
        ), patch.object(main, "extrair_metadados_bloco", return_value=METADADOS), patch.object(
            main,
            "extrair_eventos_bloco",
            return_value=eventos,
        ), patch.object(main, "build_institutional_event", return_value=None):
            publicacao_repository.salvar_publicacao.side_effect = lambda *args, **kwargs: ordem.append("publicacao") or 100
            evento_repository.salvar_evento.side_effect = lambda *args, **kwargs: ordem.append(
                f"evento-{kwargs['numero_evento']}"
            ) or kwargs["numero_evento"]
            main.run()

        self.assertEqual(ordem, ["publicacao", "evento-1", "evento-2"])
        self.assertEqual(
            [call.kwargs["publicacao_id"] for call in evento_repository.salvar_evento.call_args_list],
            [100, 100],
        )

    def test_evento_temporal_reconcilia_somente_unidade_afetada_do_pdf(self):
        conn = ConexaoTransacional()
        publicacao_repository = Mock()
        publicacao_repository.salvar_publicacao.return_value = 100
        evento_repository = Mock()
        evento_repository.salvar_evento.return_value = 1
        entity_repository = Mock()
        entity_repository.obter_ou_criar.side_effect = lambda tipo, _nome: {
            "PESSOA": 10,
            "ORGAO_PUBLICO": 20,
        }[tipo]
        timeline_reconciler = Mock()
        evento = {
            "tipo_evento": "NOMEACAO",
            "agente": {"nome": "Maria"},
            "orgao": "Secretaria",
            "entidade_origem": {},
            "entidade_destino": {},
            "evidencia": {},
        }

        with self._main_isolado(conn, publicacao_repository) as repositorios, patch.object(
            main,
            "EntityRepository",
            return_value=entity_repository,
        ), patch.object(
            main,
            "TimelineReconciler",
            return_value=timeline_reconciler,
        ), patch.object(main, "listar_pdfs", return_value=[Path("diario_3279.pdf")]), patch.object(
            main,
            "extrair_diario_id",
            return_value=3279,
        ), patch.object(main, "calcular_pdf_hash", return_value="a" * 64), patch.object(
            main,
            "extrair_texto_paginado",
            return_value=["pagina"],
        ), patch.object(main, "sanear_texto_paginado", side_effect=lambda texto: texto), patch.object(
            main,
            "serializar_texto_paginado",
            return_value="texto",
        ), patch.object(main, "extrair_data_publicacao", return_value="2026-01-01"), patch.object(
            main,
            "segmentar_publicacoes_paginado",
            return_value=["bloco"],
        ), patch.object(main, "serializar_bloco_paginado", side_effect=lambda bloco: bloco), patch.object(
            main,
            "extrair_publicacoes_pot_estruturadas",
            return_value=[],
        ), patch.object(main, "ajustar_blocos_pot_estruturais", side_effect=lambda blocos, _pot: blocos), patch.object(
            main,
            "extrair_metadados_bloco",
            return_value=METADADOS,
        ), patch.object(main, "extrair_eventos_bloco", return_value=[evento]), patch.object(
            main,
            "build_institutional_event",
            return_value=None,
        ):
            main.run()

        timeline_reconciler.reconciliar_unidade.assert_called_once_with(10, 20, "LOTACAO")

    def test_erro_no_meio_da_persistencia_de_eventos_faz_rollback_do_pdf(self):
        conn = ConexaoTransacional()
        publicacao_repository = Mock()
        publicacao_repository.salvar_publicacao.return_value = 100
        eventos = [
            {"tipo_evento": "NOMEACAO", "agente": {}, "evidencia": {}},
            {"tipo_evento": "EXONERACAO", "agente": {}, "evidencia": {}},
        ]

        with self._main_isolado(conn, publicacao_repository) as evento_repository, patch.object(
            main,
            "listar_pdfs",
            return_value=[Path("diario_3279.pdf")],
        ), patch.object(main, "extrair_diario_id", return_value=3279), patch.object(
            main,
            "calcular_pdf_hash",
            return_value="a" * 64,
        ), patch.object(
            main,
            "extrair_texto_paginado",
            return_value=["pagina"],
        ), patch.object(main, "sanear_texto_paginado", side_effect=lambda texto: texto), patch.object(
            main,
            "serializar_texto_paginado",
            return_value="texto",
        ), patch.object(main, "extrair_data_publicacao", return_value=None), patch.object(
            main,
            "segmentar_publicacoes_paginado",
            return_value=["bloco"],
        ), patch.object(main, "serializar_bloco_paginado", side_effect=lambda bloco: bloco), patch.object(
            main,
            "extrair_publicacoes_pot_estruturadas",
            return_value=[],
        ), patch.object(
            main,
            "ajustar_blocos_pot_estruturais",
            side_effect=lambda blocos, _pot: blocos,
        ), patch.object(main, "extrair_metadados_bloco", return_value=METADADOS), patch.object(
            main,
            "extrair_eventos_bloco",
            return_value=eventos,
        ), patch.object(main, "build_institutional_event", return_value=None):
            evento_repository.salvar_evento.side_effect = [1, RuntimeError("falha controlada")]
            main.run()

        self.assertEqual(conn.rollbacks, 1)
        self.assertEqual(evento_repository.salvar_evento.call_count, 2)

    @contextmanager
    def _main_isolado(self, conn, repository):
        @contextmanager
        def postgres_connection_falsa():
            yield conn

        pdf_aberto = MagicMock()
        pdf_aberto.__enter__.return_value = pdf_aberto
        evento_repository = Mock()
        timeline_reconciler = Mock()

        with patch.object(main, "postgres_connection", postgres_connection_falsa), patch.object(
            main,
            "PublicacaoRepository",
            return_value=repository,
        ), patch.object(main, "PotRepository"), patch.object(
            main,
            "EventoRepository",
            return_value=evento_repository,
        ), patch.object(main, "EntityRepository"), patch.object(
            main,
            "EntityRelationshipRepository",
        ), patch.object(
            main,
            "TimelineReconciler",
            return_value=timeline_reconciler,
        ), patch.object(
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
        ), patch.object(main.pdfplumber, "open", return_value=pdf_aberto):
            yield evento_repository