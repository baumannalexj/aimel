"""Domain objects. One model per shape, every field non-null, enums instead of booleans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class MessageState(Enum):
    UNREAD = "unread"
    READ = "read"
    DELETED = "deleted"


class Author(Enum):
    AGENT = "agent"
    HUMAN = "human"

    @property
    def counterpart(self) -> "Author":
        return Author.HUMAN if self is Author.AGENT else Author.AGENT


@dataclass(frozen=True)
class Email:
    """A core object so validation has somewhere to live as it grows."""

    address: str

    def __post_init__(self) -> None:
        if "@" not in self.address:
            raise ValueError(f"not an email address: {self.address!r}")

    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True)
class ThreadSlug:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("thread slug cannot be empty")

    @classmethod
    def from_title(cls, title: str) -> "ThreadSlug":
        slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")
        return cls(slug[:60])

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("session id cannot be empty")

    @property
    def short(self) -> str:
        return self.value[:8]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class NewCorrespondence:
    """Not yet persisted, so it has no id and no created_at — those are the database's to assign."""

    session: SessionId
    thread: ThreadSlug
    subject: str
    sender: Email
    recipient: Email
    author: Author
    rfc_message_id: str
    in_reply_to: str
    references: tuple[str, ...]
    body_html: str
    body_text: str
    sent_at: datetime


@dataclass(frozen=True)
class Correspondence:
    """Everything true of a persisted message regardless of what state it is in.

    `id` is the row's uuid. The surrogate primary key never leaves the repository.
    """

    id: str
    created_at: datetime
    session: SessionId
    thread: ThreadSlug
    subject: str
    sender: Email
    recipient: Email
    author: Author
    rfc_message_id: str
    in_reply_to: str
    references: tuple[str, ...]
    body_html: str
    body_text: str
    sent_at: datetime

    @property
    def preview(self) -> str:
        body = self.body_text or re.sub(r"<[^>]+>", " ", self.body_html)
        return " ".join(body.split())[:120]


@dataclass(frozen=True)
class UnreadMessage:
    content: Correspondence

    @property
    def state(self) -> MessageState:
        return MessageState.UNREAD


@dataclass(frozen=True)
class ReadMessage:
    content: Correspondence
    read_at: datetime

    @property
    def state(self) -> MessageState:
        return MessageState.READ


@dataclass(frozen=True)
class DeletedMessage:
    content: Correspondence
    deleted_at: datetime
    previous_state: MessageState

    @property
    def state(self) -> MessageState:
        return MessageState.DELETED


Message = UnreadMessage | ReadMessage | DeletedMessage
LiveMessage = UnreadMessage | ReadMessage


def now() -> datetime:
    return datetime.now(timezone.utc)
