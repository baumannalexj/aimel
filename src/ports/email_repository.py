from __future__ import annotations

from abc import ABC, abstractmethod

from domain.message import (
    DeletedMessage,
    Email,
    EmailThread,
    LiveMessage,
    Message,
    MessageState,
    NewCorrespondence,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
)
from domain.thread import ThreadSummary


class IEmailRepository(ABC):
    """Persistence for correspondence. Callers never learn where it is stored."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Create anything missing. Safe to call on every start."""

    @abstractmethod
    def resolve_thread(self, session: SessionId, slug: ThreadSlug) -> EmailThread:
        """The thread for this slug, reusing its id if it already exists and minting one if not."""

    @abstractmethod
    def add(self, correspondence: NewCorrespondence) -> UnreadMessage:
        """Persist new mail. The id and created_at come back from the schema."""

    @abstractmethod
    def find(self, message_id: str) -> Message | None:
        """Look a message up whatever state it is in."""

    @abstractmethod
    def list_unread(self, recipient: Email, limit: int = 50) -> list[UnreadMessage]:
        """Unread mail for a mailbox, newest first."""

    @abstractmethod
    def list_unread_in_thread(
        self, recipient: Email, thread: EmailThread, limit: int = 50
    ) -> list[UnreadMessage]:
        """Unread mail for a mailbox on one thread, newest first."""

    @abstractmethod
    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        """Anything in one state, newest first."""

    @abstractmethod
    def mark_read(self, message: UnreadMessage) -> ReadMessage:
        """Move it to the read table. `read_at` is stamped by the schema, not the caller."""

    @abstractmethod
    def soft_delete(self, message: LiveMessage) -> DeletedMessage:
        """Move it to the deleted table. `deleted_at` is stamped by the schema."""

    @abstractmethod
    def exists_by_rfc_id(self, rfc_message_id: str) -> bool:
        """Whether intake has already claimed this message, so draining stays idempotent."""

    @abstractmethod
    def history(self, session: SessionId, thread: EmailThread) -> list[Message]:
        """Every message on a thread, newest first, deleted ones included."""

    @abstractmethod
    def threads(self, session: SessionId) -> list[ThreadSummary]:
        """Threads for a session, most recently updated first."""
