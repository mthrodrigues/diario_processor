import time
from contextlib import contextmanager

from config import get_postgres_config


class PostgresConnectionPool:
    def __init__(self, pg_config=None):
        self.config = pg_config or get_postgres_config()
        self._pool = None

    def _criar_pool(self):
        try:
            from psycopg2.pool import SimpleConnectionPool
        except ImportError as exc:
            raise RuntimeError(
                "psycopg2-binary nao esta instalado. Instale as dependencias do requirements.txt."
            ) from exc

        return SimpleConnectionPool(
            self.config.min_pool_size,
            self.config.max_pool_size,
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.db,
            user=self.config.user,
            password=self.config.password,
            connect_timeout=self.config.connect_timeout,
            application_name="diario_processor",
        )

    def _obter_pool(self):
        if self._pool is None:
            self._pool = self._executar_com_retry(self._criar_pool)

        return self._pool

    def _executar_com_retry(self, func):
        ultima_excecao = None

        for tentativa in range(1, self.config.retry_attempts + 1):
            try:
                return func()
            except Exception as exc:
                ultima_excecao = exc

                if tentativa >= self.config.retry_attempts:
                    break

                time.sleep(self.config.retry_delay_seconds)

        raise ultima_excecao

    @contextmanager
    def connection(self):
        pool = self._obter_pool()
        conn = self._executar_com_retry(pool.getconn)

        try:
            yield conn
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            pool.putconn(conn)

    def close(self):
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None


_default_pool = None


def get_connection_pool():
    global _default_pool

    if _default_pool is None:
        _default_pool = PostgresConnectionPool()

    return _default_pool


@contextmanager
def postgres_connection():
    with get_connection_pool().connection() as conn:
        yield conn
