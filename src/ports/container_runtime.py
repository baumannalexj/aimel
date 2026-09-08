from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IContainerRuntime(ABC):
    """Starts and stops the intake spool. Core never touches this; only the CLI does."""

    @abstractmethod
    def up(self, mail_dir: Path) -> None:
        """Start the spool, idempotently."""

    @abstractmethod
    def down(self, mail_dir: Path) -> None:
        """Stop it. Mail survives in the database."""

    @abstractmethod
    def restart(self, mail_dir: Path) -> None:
        """Bounce it."""

    @abstractmethod
    def logs(self, mail_dir: Path, follow: bool = False) -> int:
        """Stream its logs, returning the exit status."""

    @abstractmethod
    def wait_until_ready(self, health_url: str, timeout_seconds: int = 30) -> bool:
        """Whether the spool answered before the timeout."""
