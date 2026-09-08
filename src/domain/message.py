"""Domain objects. One model per shape, every field non-null, enums instead of booleans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from domain.domain_model import DomainModel


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
class Email(DomainModel):
    """A core object so validation has somewhere to live as it grows."""

    address: str

    def __post_init__(self) -> None:
        if "@" not in self.address:
            raise ValueError(f"not an email address: {self.address!r}")

    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True)
class EmailSubject(DomainModel):
    """The thread's context. Set once, when the thread opens."""

    text: str

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("subject cannot be empty")

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class SessionId(DomainModel):
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
class NewCorrespondence(DomainModel):
    """Not yet persisted, so it has no id and no created_at — those are the database's to assign."""

    session: SessionId
    subject: EmailSubject
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
class Correspondence(DomainModel):
    """Everything true of a persisted message regardless of what state it is in.

    `id` is the row's uuid. The surrogate primary key never leaves the repository.
    """

    id: str
    created_at: datetime
    thread_uuid: str
    session: SessionId
    subject: EmailSubject
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
        """Quoted history is stripped, otherwise every reply previews as the whole thread."""
        body = self.body_text or self.body_html
        body = re.sub(r"<hr><details.*?</details>", " ", body, flags=re.S)
        return " ".join(re.sub(r"<[^>]+>", " ", body).split())[:120]


@dataclass(frozen=True)
class UnreadMessage(DomainModel):
    content: Correspondence

    @property
    def state(self) -> MessageState:
        return MessageState.UNREAD


@dataclass(frozen=True)
class ReadMessage(DomainModel):
    content: Correspondence
    read_at: datetime

    @property
    def state(self) -> MessageState:
        return MessageState.READ


@dataclass(frozen=True)
class DeletedMessage(DomainModel):
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
