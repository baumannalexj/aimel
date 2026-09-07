from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.domain_model import DomainModel
from domain.message import EmailSubject, EmailThread, SessionId


@dataclass(frozen=True)
class ThreadSummary(DomainModel):
    session: SessionId
    thread: EmailThread
    subject: EmailSubject
    message_count: int
    updated_at: datetime
