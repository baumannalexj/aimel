"""Domain objects. One model per shape, every field non-null, enums instead of booleans."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
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
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise ValueError(f"not an email address: {self.value!r}")

    def __str__(self) -> str:
        return self.value


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
class Correspondence:
    """Everything true of a message regardless of what state it is in."""

    id: str
    session: SessionId
    thread: ThreadSlug
    subject: str
    sender: EmailAddress
    recipient: EmailAddress
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

    def mark_read(self, when: datetime | None = None) -> "ReadMessage":
        return ReadMessage(content=self.content, read_at=when or now())

    def soft_delete(self, when: datetime | None = None) -> "DeletedMessage":
        return DeletedMessage(content=self.content, deleted_at=when or now())


@dataclass(frozen=True)
class ReadMessage:
    content: Correspondence
    read_at: datetime

    @property
    def state(self) -> MessageState:
        return MessageState.READ

    def soft_delete(self, when: datetime | None = None) -> "DeletedMessage":
        return DeletedMessage(content=self.content, deleted_at=when or now(), read_at=self.read_at)


@dataclass(frozen=True)
class DeletedMessage:
    content: Correspondence
    deleted_at: datetime
    read_at: datetime | None = None

    @property
    def state(self) -> MessageState:
        return MessageState.DELETED


Message = UnreadMessage | ReadMessage | DeletedMessage


def now() -> datetime:
    return datetime.now(timezone.utc)
