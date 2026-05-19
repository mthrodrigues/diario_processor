import re
from pathlib import Path

from config import get_postgres_config


MIGRATIONS_DIR = Path(__file__).resolve().parent


def run_migrations(conn, schema=None):
    schema = schema or get_postgres_config().schema
    schema_sql = quote_ident(schema)
    _ensure_schema(conn, schema_sql)
    _ensure_migration_table(conn, schema_sql)

    aplicadas = _migrations_aplicadas(conn, schema_sql)

    for migration_path in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version = migration_path.name.split("_", 1)[0]

        if version in aplicadas:
            continue

        sql = migration_path.read_text(encoding="utf-8").format(schema=schema_sql)

        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute(
                f"""
                INSERT INTO {schema_sql}.schema_migrations (version, name)
                VALUES (%s, %s)
                """,
                (version, migration_path.name),
            )


def quote_ident(identifier):
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", identifier):
        raise ValueError(f"Identificador SQL invalido: {identifier}")

    return f'"{identifier}"'


def _ensure_schema(conn, schema_sql):
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_sql}")


def _ensure_migration_table(conn, schema_sql):
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema_sql}.schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def _migrations_aplicadas(conn, schema_sql):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT version FROM {schema_sql}.schema_migrations")
        return {linha[0] for linha in cursor.fetchall()}
