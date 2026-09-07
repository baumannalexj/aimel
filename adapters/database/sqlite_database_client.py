from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ports.database_client import IDatabaseClient, Params, Row


def start(database: Path, timeout: float = 5.0) -> sqlite3.Connection:
    """Open the one connection the process will share. Called by DatabaseModule."""
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        path, timeout=timeout, isolation_level=None, check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


class SqliteDatabaseClient(IDatabaseClient):
    """Wraps the connection singleton. Executes SQL, never writes any."""

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._lock = threading.RLock()

    def execute(self, sql: str, params: Params = ()) -> None:
        with self._lock:
            self._connection.execute(sql, params)

    def query(self, sql: str, params: Params = ()) -> list[Row]:
        with self._lock:
            rows = self._connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield
            except Exception:
                self._connection.execute("ROLLBACK")
                raise
            self._connection.execute("COMMIT")

    def close(self) -> None:
        with self._lock:
            self._connection.close()
