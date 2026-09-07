"""Request objects. Every field is a domain type — no primitives reach the resource."""

from __future__ import annotations

from dataclasses import dataclass

from domain.message import Author, SessionId, ThreadSlug


@dataclass(frozen=True)
class SendRequest:
    session: SessionId
    thread: ThreadSlug
    title: str
    html: str
    text: str
    author: Author
    include_history: bool


@dataclass(frozen=True)
class PollRequest:
    session: SessionId
    thread: ThreadSlug | None
    mailbox_owner: Author
    limit: int


@dataclass(frozen=True)
class ThreadRequest:
    session: SessionId
    thread: ThreadSlug


@dataclass(frozen=True)
class SessionRequest:
    session: SessionId


@dataclass(frozen=True)
class MessageRequest:
    message_id: str


@dataclass(frozen=True)
class ListRequest:
    limit: int


@dataclass(frozen=True)
class DrainRequest:
    purge: bool
    limit: int
