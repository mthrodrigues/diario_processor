import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _carregar_dotenv(caminho=None):
    caminho = Path(caminho or PROJECT_ROOT / ".env")

    if not caminho.exists():
        return

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()

        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave, valor)


_carregar_dotenv()


APP_ENV = os.getenv("APP_ENV", "dev")
BASE_DIARIO_PATH = Path(os.getenv("BASE_DIARIO_PATH", "C:/automacoes/diario_bot"))

# Compatibilidade local/testes legados. A persistencia institucional deve usar Postgres.
DATABASE_PATH = Path(os.getenv("SQLITE_DATABASE_PATH", "diario_processor.db"))


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    db: str
    user: str
    password: str
    schema: str
    connect_timeout: int
    retry_attempts: int
    retry_delay_seconds: float
    min_pool_size: int
    max_pool_size: int


def get_postgres_config():
    return PostgresConfig(
        host=_obrigatorio("POSTGRES_HOST"),
        port=int(_obrigatorio("POSTGRES_PORT")),
        db=_obrigatorio("POSTGRES_DB"),
        user=_obrigatorio("POSTGRES_USER"),
        password=_obrigatorio("POSTGRES_PASSWORD"),
        schema=os.getenv("POSTGRES_SCHEMA", "diario"),
        connect_timeout=int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5")),
        retry_attempts=int(os.getenv("POSTGRES_RETRY_ATTEMPTS", "3")),
        retry_delay_seconds=float(os.getenv("POSTGRES_RETRY_DELAY_SECONDS", "0.5")),
        min_pool_size=int(os.getenv("POSTGRES_MIN_POOL_SIZE", "1")),
        max_pool_size=int(os.getenv("POSTGRES_MAX_POOL_SIZE", "5")),
    )


def _obrigatorio(nome):
    valor = os.getenv(nome)

    if valor is None or valor.strip() == "":
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")

    return valor
