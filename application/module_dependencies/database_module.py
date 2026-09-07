from __future__ import annotations

from adapters.database import sqlite_database_client
from adapters.database.sqlite_database_client import SqliteDatabaseClient
from common.config import DatabaseConfig
from ports.database_client import IDatabaseClient


class DatabaseModule:
    """Owns the driver singleton for the whole process."""

    def __init__(self, config: DatabaseConfig):
        self._connection = sqlite_database_client.start(config.path, config.timeout_seconds)
        self._client = SqliteDatabaseClient(self._connection)

    def provide_database_client(self) -> IDatabaseClient:
        return self._client

    def close(self) -> None:
        self._client.close()
