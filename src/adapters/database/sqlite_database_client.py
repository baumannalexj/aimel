from __future__ import annotations

import re
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ports.database_client import IDatabaseClient, Params, Row

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqliteSessionFactory:
    """Makes driver sessions. Autocommit by default; transactions ask for one without it."""

    def __init__(self, database: Path, timeout: float = 5.0):
        self._path = Path(database)
        self._timeout = timeout
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def open(self, autocommit: bool = True) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path, timeout=self._timeout, check_same_thread=False
        )
        connection.row_factory = sqlite3.Row
        connection.autocommit = autocommit
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection


class SqliteDatabaseClient(IDatabaseClient):
    def __init__(self, factory: SqliteSessionFactory, connection: sqlite3.Connection | None = None):
        self._factory = factory
        self._connection = connection if connection is not None else factory.open(autocommit=True)
        self._lock = threading.RLock()

    def execute(self, sql: str, params: Params = ()) -> None:
        with self._lock:
            self._connection.execute(sql, params)

    def query(self, sql: str, params: Params = ()) -> list[Row]:
        with self._lock:
            rows = self._connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    @contextmanager
    def transaction(self) -> Iterator[IDatabaseClient]:
        connection = self._factory.open(autocommit=False)
        try:
            yield SqliteDatabaseClient(self._factory, connection)
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            connection.close()

    def identifier(self, name: str) -> str:
        if not IDENTIFIER.match(name):
            raise ValueError(f"not a usable sql identifier: {name!r}")
        return f'"{name}"'

    def close(self) -> None:
        with self._lock:
            self._connection.close()
