from __future__ import annotations

from dataclasses import dataclass

from domain.message import Author, Email, SessionId, ThreadSlug


@dataclass(frozen=True)
class Draft:
    """What a caller wants sent. Constructed at the edge, before core is called."""

    session: SessionId
    thread: ThreadSlug
    subject: str
    sender: Email
    recipient: Email
    author: Author
    body_html: str
    body_text: str
    include_history: bool = True


@dataclass(frozen=True)
class Envelope:
    """What actually goes on the wire, once core has resolved the reply chain."""

    sender: Email
    recipient: Email
    subject: str
    session: SessionId
    thread: ThreadSlug
    in_reply_to: str
    references: tuple[str, ...]
