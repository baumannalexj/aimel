from __future__ import annotations

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from common.config import DatabaseConfig
from ports.database_client import IDatabaseClient


class DatabaseModule:
    """Owns the driver session factory and the shared autocommit client."""

    def __init__(self, config: DatabaseConfig):
        self._factory = SqliteSessionFactory(config.path, config.timeout_seconds)
        self._client = SqliteDatabaseClient(self._factory)

    def provide_database_client(self) -> IDatabaseClient:
        return self._client

    def close(self) -> None:
        self._client.close()
