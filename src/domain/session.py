from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.domain_model import DomainModel
from domain.message import SessionId


@dataclass(frozen=True)
class AgentSession(DomainModel):
    """One agent, registered the moment its first email is seen.

    `id` is the row's own uuid, kept distinct from `session_id` so the surrogate identity never
    has to change even if the natural key ever did. Colour is deliberately not a field here —
    `SessionColorPalette` derives it from `session_id` at request time, so there is nothing on
    this object that could drift out of sync with the palette.
    """

    id: str
    session_id: SessionId
    created_at: datetime
    last_seen_at: datetime
    email_count: int

    def __post_init__(self) -> None:
        if self.email_count < 0:
            raise ValueError("email_count cannot be negative")
