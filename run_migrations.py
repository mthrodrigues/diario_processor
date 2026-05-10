from infra.db.connection import postgres_connection
from infra.db.migrations.runner import run_migrations

with postgres_connection() as conn:
    run_migrations(conn)

print("Migrations executadas com sucesso!")