from __future__ import annotations

from abc import ABC, abstractmethod

from domain.commands import SentEmail
from domain.message import (
    DeletedMessage,
    Email,
    LiveMessage,
    Message,
    MessageState,
    ReadMessage,
    SessionId,
    UnreadMessage,
)
from domain.thread import ThreadSummary


class IEmailRepository(ABC):
    """Persistence for correspondence. Thread identity is assigned here, not by callers."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Create anything missing. Safe to call on every start."""

    @abstractmethod
    def add_new_thread(self, sent: SentEmail) -> UnreadMessage:
        """Persist the first email of a thread. The schema mints the thread uuid."""

    @abstractmethod
    def add_reply(self, sent: SentEmail, in_reply_to_email_id: str) -> UnreadMessage:
        """Persist a reply, inheriting the thread uuid of the email it answers."""

    @abstractmethod
    def find(self, email_id: str) -> Message | None:
        """Look an email up whatever state it is in."""

    @abstractmethod
    def find_by_rfc_id(self, rfc_message_id: str) -> Message | None:
        """Look an email up by its wire Message-ID, for anchoring intake replies."""

    @abstractmethod
    def list_unread(self, recipient: Email, limit: int = 50) -> list[UnreadMessage]:
        """Unread mail for a mailbox, newest first."""

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
    def history_for_email(self, email_id: str) -> list[Message]:
        """Every email sharing that email's thread, newest first, deleted ones included."""

    @abstractmethod
    def threads(self, session: SessionId) -> list[ThreadSummary]:
        """Threads for one session, most recently updated first."""

    @abstractmethod
    def all_threads(self, limit: int = 200) -> list[ThreadSummary]:
        """Threads across every session, so one inbox can span several agents."""

    @abstractmethod
    def threads_for_mailbox(self, recipient: Email, limit: int = 200) -> list[ThreadSummary]:
        """Threads where that mailbox was addressed at least once, deleted mail included.

        A thread stays in the mailbox even after the conversation moves on to other
        agents replying among themselves — it only has to have included the mailbox once.
        """
