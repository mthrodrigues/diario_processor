"""Configuração central de logging persistente do diario_processor.

Regra: sucesso gera uma única linha; erro gera contexto completo + traceback.
Não trata configuração de aplicação (isso é responsabilidade de config.py).
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

LOGGER_NAME = "diario_processor"

_FORMATO = "%(asctime)s | %(levelname)s | %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"

_NAO_INFORMADO = "?"


def setup_logging(log_dir=None, log_file="diario_processor.log", level=None):
    """Configura (uma vez) o logger persistente e retorna a instância."""
    log_dir = Path(log_dir) if log_dir else Path(os.getenv("LOG_DIR", PROJECT_ROOT / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    nivel = level or os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(nivel)
    logger.propagate = False

    ja_configurado = any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename) == (log_dir / log_file).resolve()
        for handler in logger.handlers
    )

    if not ja_configurado:
        handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(_FORMATO, datefmt=_DATEFMT))
        logger.addHandler(handler)

    return logger


def get_logger():
    """Retorna o logger persistente (assume que setup_logging já foi chamado)."""
    return logging.getLogger(LOGGER_NAME)


def novo_run_id():
    """Identificador simples, determinístico e legível para uma execução."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def log_sucesso(logger, run_id, diario_id, arquivo):
    """Registra uma única linha para o processamento bem-sucedido de um Diário."""
    logger.info(
        "run=%s | diario=%s | arquivo=%s | etapa=processamento | mensagem=Processamento concluído com sucesso",
        run_id,
        diario_id if diario_id is not None else _NAO_INFORMADO,
        arquivo if arquivo is not None else _NAO_INFORMADO,
    )


def log_erro(logger, run_id, mensagem, diario_id=None, arquivo=None, bloco=None, etapa=None, exc_info=True):
    """Registra um erro com contexto disponível e traceback (via exc_info)."""
    logger.error(
        "run=%s | diario=%s | arquivo=%s | bloco=%s | etapa=%s | mensagem=%s",
        run_id,
        diario_id if diario_id is not None else _NAO_INFORMADO,
        arquivo if arquivo is not None else _NAO_INFORMADO,
        bloco if bloco is not None else _NAO_INFORMADO,
        etapa if etapa is not None else _NAO_INFORMADO,
        mensagem,
        exc_info=exc_info,
    )
