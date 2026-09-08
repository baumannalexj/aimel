"""What a caller intends. One shape per operation, so no field is ever meaningless."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.domain_model import DomainModel
from domain.message import Actor, Email, EmailSubject, HtmlBody, SessionId


class IncludeHistory(Enum):
    """Enum rather than a flag, so "just the last reply" can be added without a second boolean."""

    NONE = "none"
    ALL = "all"


@dataclass(frozen=True)
class EmailSendNewThread(DomainModel):
    """Opens a thread. Carries no thread id — the database mints one."""

    session: SessionId
    subject: EmailSubject
    sender: Email
    recipient: Email
    author: Actor
    body_html: HtmlBody
    body_text: str


@dataclass(frozen=True)
class EmailReply(DomainModel):
    """Continues a thread by pointing at the email being answered."""

    session: SessionId
    in_reply_to_email_id: str
    sender: Email
    recipient: Email
    author: Actor
    body_html: HtmlBody
    body_text: str
    include_history: IncludeHistory = IncludeHistory.ALL

    def __post_init__(self) -> None:
        if not self.in_reply_to_email_id:
            raise ValueError("a reply must name the email it answers")


@dataclass(frozen=True)
class EmailDelete(DomainModel):
    email_id: str

    def __post_init__(self) -> None:
        if not self.email_id:
            raise ValueError("a delete must name an email")


@dataclass(frozen=True)
class SentEmail(DomainModel):
    """What went on the wire, ready to persist. The thread is the repository's business."""

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
