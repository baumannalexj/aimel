from __future__ import annotations

from abc import ABC, abstractmethod

from domain.message import (
    DeletedMessage,
    Message,
    MessageState,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
)
from domain.thread import Thread


class IEmailRepository(ABC):
    """Persistence for correspondence. Callers never learn where it is stored."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Create anything missing. Safe to call on every start."""

    @abstractmethod
    def add(self, message: UnreadMessage) -> UnreadMessage:
        """Store a newly sent or newly captured message."""

    @abstractmethod
    def find(self, message_id: str) -> Message | None:
        """Look a message up whatever state it is in."""

    @abstractmethod
    def list_unread(
        self, recipient: str = "", thread: ThreadSlug | None = None, limit: int = 50
    ) -> list[UnreadMessage]:
        """Unread mail, newest first."""

    @abstractmethod
    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        """Anything in one state, newest first."""

    @abstractmethod
    def mark_read(self, message: ReadMessage) -> ReadMessage:
        """Move a message into the read table."""

    @abstractmethod
    def soft_delete(self, message: DeletedMessage) -> DeletedMessage:
        """Move a message into the deleted table, stamping deleted_at."""

    @abstractmethod
    def exists_by_rfc_id(self, rfc_message_id: str) -> bool:
        """Whether intake has already claimed this message, so draining stays idempotent."""

    @abstractmethod
    def history(self, session: SessionId, thread: ThreadSlug) -> list[Message]:
        """Every message on a thread, newest first, deleted ones included."""

    @abstractmethod
    def threads(self, session: SessionId) -> list[Thread]:
        """Threads for a session, most recently updated first."""
