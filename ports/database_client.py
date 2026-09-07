from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import AbstractContextManager
from typing import Any

Params = Mapping[str, Any] | Sequence[Any]
Row = dict[str, Any]


class IDatabaseClient(ABC):
    """Owns the driver connection. Callers hand it SQL; it never composes any."""

    @abstractmethod
    def execute(self, sql: str, params: Params = ()) -> None:
        """Run a statement that returns nothing."""

    @abstractmethod
    def query(self, sql: str, params: Params = ()) -> list[Row]:
        """Run a statement and return rows as plain dicts."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[None]:
        """Group statements so they commit or roll back together."""

    @abstractmethod
    def close(self) -> None:
        """Release the connection."""
