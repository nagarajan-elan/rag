from typing import Any

from psycopg2 import pool

from app.core.config import get_settings


class Database:
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or get_settings().database_url
        if not self._dsn:
            raise RuntimeError("DATABASE_URL must be configured")
        self._pool: pool.ThreadedConnectionPool | None = None

    def initialize(self) -> None:
        if self._pool is None:
            self._pool = pool.ThreadedConnectionPool(
                1,
                20,
                dsn=self._dsn,
            )

    def get_connection(self) -> Any:
        if self._pool is None:
            self.initialize()
        assert self._pool is not None
        return self._pool.getconn()

    def release_connection(self, connection: Any) -> None:
        if self._pool is not None:
            self._pool.putconn(connection)


_db = Database()


def get_connection() -> Any:
    return _db.get_connection()


def initialize_database() -> None:
    _db.initialize()
