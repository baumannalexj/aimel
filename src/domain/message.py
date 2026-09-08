"""Domain objects. One model per shape, every field non-null, enums instead of booleans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from domain.domain_model import DomainModel

TAG = re.compile(r"<[^>]+>")
QUOTED_HISTORY = re.compile(r"<hr><details.*?</details>", re.S)


class MessageState(Enum):
    UNREAD = "unread"
    READ = "read"
    DELETED = "deleted"


class Actor(Enum):
    """Who wrote it. Vendor-neutral, so a second agent kind costs one member."""

    HUMAN = "human"
    AI_AGENT = "ai_agent"

    @property
    def counterpart(self) -> "Actor":
        return Actor.HUMAN if self is Actor.AI_AGENT else Actor.AI_AGENT


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
class HtmlBody(DomainModel):
    """An email body. Pydantic ships no HTML type, so this is where that behaviour lives."""

    markup: str

    def to_plain_text(self) -> str:
        """Tags become spaces, otherwise block boundaries weld words together."""
        return " ".join(TAG.sub(" ", self.markup).split())

    def without_quoted_history(self) -> "HtmlBody":
        return HtmlBody(QUOTED_HISTORY.sub(" ", self.markup))

    def preview(self, limit: int = 120) -> str:
        """What a list view shows: this email only, never the thread quoted beneath it."""
        return self.without_quoted_history().to_plain_text()[:limit]

    def followed_by(self, more: str) -> "HtmlBody":
        return HtmlBody(self.markup + more)

    def __bool__(self) -> bool:
        return bool(self.markup)

    def __str__(self) -> str:
        return self.markup


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
class Correspondence(DomainModel):
    """Everything true of a persisted email regardless of what state it is in.

    `id` is the row's uuid. The surrogate primary key never leaves the repository.
    """

    id: str
    created_at: datetime
    thread_uuid: str
    session: SessionId
    subject: EmailSubject
    sender: Email
    recipient: Email
    author: Actor
    rfc_message_id: str
    in_reply_to: str
    references: tuple[str, ...]
    body_html: HtmlBody
    body_text: str
    sent_at: datetime

    @property
    def preview(self) -> str:
        if self.body_html:
            return self.body_html.preview()
        return " ".join(self.body_text.split())[:120]


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
