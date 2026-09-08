from __future__ import annotations

from dataclasses import dataclass

from domain.domain_model import DomainModel
from domain.message import Email, EmailSubject, SessionId


@dataclass(frozen=True)
class Envelope(DomainModel):
    """What actually goes on the wire, once core has resolved the reply chain."""

    sender: Email
    recipient: Email
    subject: EmailSubject
    session: SessionId
    in_reply_to: str
    references: tuple[str, ...]
