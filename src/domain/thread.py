from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.message import SessionId, ThreadSlug


@dataclass(frozen=True)
class Thread:
    session: SessionId
    slug: ThreadSlug
    subject: str
    message_count: int
    updated_at: datetime
