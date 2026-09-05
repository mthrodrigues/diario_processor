import logging
import tempfile
import unittest
from pathlib import Path

from logging_setup import LOGGER_NAME, log_erro, log_sucesso, novo_run_id, setup_logging


class LoggingSetupTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_dir = Path(self._tmpdir.name)

    def tearDown(self):
        logger = logging.getLogger(LOGGER_NAME)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        self._tmpdir.cleanup()

    def _ler_log(self):
        arquivo = self.log_dir / "diario_processor.log"
        return arquivo.read_text(encoding="utf-8")

    def test_setup_logging_cria_arquivo_no_diretorio_esperado(self):
        setup_logging(log_dir=self.log_dir, level="INFO")

        arquivo = self.log_dir / "diario_processor.log"
        self.assertTrue(arquivo.exists())

    def test_setup_logging_aplica_nivel_configurado(self):
        logger = setup_logging(log_dir=self.log_dir, level="WARNING")

        logger.info("mensagem que não deveria aparecer")
        logger.warning("mensagem que deveria aparecer")

        conteudo = self._ler_log()
        self.assertNotIn("não deveria aparecer", conteudo)
        self.assertIn("deveria aparecer", conteudo)

    def test_log_sucesso_gera_unica_mensagem_com_contexto(self):
        logger = setup_logging(log_dir=self.log_dir, level="INFO")
        run_id = novo_run_id()

        log_sucesso(logger, run_id, diario_id="3388", arquivo="diario_3388.pdf")

        conteudo = self._ler_log()
        linhas = [linha for linha in conteudo.splitlines() if linha.strip()]
        self.assertEqual(len(linhas), 1)
        self.assertIn(f"run={run_id}", linhas[0])
        self.assertIn("diario=3388", linhas[0])
        self.assertIn("arquivo=diario_3388.pdf", linhas[0])
        self.assertIn("Processamento concluído com sucesso", linhas[0])

    def test_log_erro_registra_contexto_e_traceback(self):
        logger = setup_logging(log_dir=self.log_dir, level="INFO")
        run_id = novo_run_id()

        try:
            raise ValueError("falha simulada de salvar_publicacao")
        except ValueError as e:
            log_erro(
                logger,
                run_id,
                str(e),
                diario_id="3388",
                arquivo="diario_3388.pdf",
                bloco=5,
                etapa="salvar_publicacao",
            )

        conteudo = self._ler_log()
        self.assertIn("ERROR", conteudo)
        self.assertIn(f"run={run_id}", conteudo)
        self.assertIn("diario=3388", conteudo)
        self.assertIn("arquivo=diario_3388.pdf", conteudo)
        self.assertIn("bloco=5", conteudo)
        self.assertIn("etapa=salvar_publicacao", conteudo)
        self.assertIn("falha simulada de salvar_publicacao", conteudo)
        self.assertIn("Traceback (most recent call last)", conteudo)

    def test_log_erro_antes_de_diario_id_nao_mascara_excecao(self):
        logger = setup_logging(log_dir=self.log_dir, level="INFO")
        run_id = novo_run_id()

        diario_id = None
        i = None

        try:
            raise RuntimeError("falha antes de extrair_diario_id")
        except RuntimeError as e:
            log_erro(
                logger,
                run_id,
                str(e),
                diario_id=diario_id,
                arquivo="diario_3388.pdf",
                bloco=i,
                etapa="extrair_diario_id",
            )

        conteudo = self._ler_log()
        self.assertIn("diario=?", conteudo)
        self.assertIn("bloco=?", conteudo)
        self.assertIn("falha antes de extrair_diario_id", conteudo)
        self.assertIn("Traceback (most recent call last)", conteudo)

    def test_erros_nao_fatais_registram_sem_interromper(self):
        logger = setup_logging(log_dir=self.log_dir, level="INFO")
        run_id = novo_run_id()

        for etapa in ("enriquecimento_contextual", "publicar_evento_canonico"):
            try:
                raise Exception(f"falha não fatal em {etapa}")
            except Exception as e:
                log_erro(
                    logger,
                    run_id,
                    str(e),
                    diario_id="3388",
                    bloco=2,
                    etapa=etapa,
                )

        conteudo = self._ler_log()
        self.assertIn("etapa=enriquecimento_contextual", conteudo)
        self.assertIn("etapa=publicar_evento_canonico", conteudo)


if __name__ == "__main__":
    unittest.main()
