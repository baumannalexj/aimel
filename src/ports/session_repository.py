from __future__ import annotations

from abc import ABC, abstractmethod

from domain.message import SessionId
from domain.session import AgentSession


class ISessionRepository(ABC):
    """Persistence for agent sessions. A session exists once its first email is registered."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Create anything missing. Safe to call on every start."""

    @abstractmethod
    def register(self, session_id: SessionId) -> AgentSession:
        """Record that a session sent mail. Idempotent — safe to call on every email, not just the first."""

    @abstractmethod
    def find(self, session_id: SessionId) -> AgentSession | None:
        """Look a session up by its Claude uuid."""

    @abstractmethod
    def list_all(self) -> list[AgentSession]:
        """Every known session, most recently active first."""
