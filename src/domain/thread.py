from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.domain_model import DomainModel
from domain.message import EmailSubject, SessionId


@dataclass(frozen=True)
class ThreadSummary(DomainModel):
    """Rollup behind the threads listing. thread_uuid is assigned by the repository."""

    session: SessionId
    thread_uuid: str
    subject: EmailSubject
    message_count: int
    latest_email_id: str
    updated_at: datetime
