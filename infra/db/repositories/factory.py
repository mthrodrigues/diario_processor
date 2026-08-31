from contextlib import contextmanager

from config import get_postgres_config
from infra.db.connection import postgres_connection
from infra.db.migrations.runner import run_migrations
from infra.db.repositories.publicacao_repository import PublicacaoRepository
from infra.db.repositories.pot_repository import PotRepository

@contextmanager
def publicacao_repository():
    with postgres_connection() as conn:
        run_migrations(conn, schema=get_postgres_config().schema)
        yield PublicacaoRepository(conn, schema=get_postgres_config().schema)

@contextmanager
def pot_repository():
    with postgres_connection() as conn:
        run_migrations(
            conn,
            schema=get_postgres_config().schema,
        )
        yield PotRepository(
            conn,
            schema=get_postgres_config().schema,
        )