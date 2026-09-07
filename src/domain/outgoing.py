from __future__ import annotations

from dataclasses import dataclass

from domain.domain_model import DomainModel
from domain.message import Author, Email, EmailSubject, EmailThread, SessionId


@dataclass(frozen=True)
class Draft(DomainModel):
    """What a caller wants sent. Constructed at the edge, before core is called."""

    session: SessionId
    thread: EmailThread
    subject: EmailSubject
    sender: Email
    recipient: Email
    author: Author
    body_html: str
    body_text: str
    include_history: bool = True


@dataclass(frozen=True)
class Envelope(DomainModel):
    """What actually goes on the wire, once core has resolved the reply chain."""

    sender: Email
    recipient: Email
    subject: EmailSubject
    session: SessionId
    thread: EmailThread
    in_reply_to: str
    references: tuple[str, ...]
