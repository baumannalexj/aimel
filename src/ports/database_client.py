from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from typing import Any

Params = Mapping[str, Any] | Sequence[Any]
Row = dict[str, Any]


class IDatabaseClient(ABC):
    """Owns the driver session. Callers hand it SQL; it never composes any."""

    @abstractmethod
    def execute(self, sql: str, params: Params = ()) -> None:
        """Run a statement that returns nothing."""

    @abstractmethod
    def query(self, sql: str, params: Params = ()) -> list[Row]:
        """Run a statement and return rows as plain dicts."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager["IDatabaseClient"]:
        """Open a non-autocommit session and yield a client bound to it.

        Commits when the block exits cleanly, rolls back on any exception. Statements must go
        through the yielded client — the outer client is autocommit and would not be enrolled.
        """

    @abstractmethod
    def identifier(self, name: str) -> str:
        """Validate and quote a table or column name.

        Values always travel as named binds, so this is the only sanctioned way to put a name into
        a statement. It rejects anything that is not a plain identifier rather than trusting it.
        """

    @abstractmethod
    def close(self) -> None:
        """Release the session."""
