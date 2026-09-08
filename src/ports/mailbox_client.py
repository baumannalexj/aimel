from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CapturedMessage:
    """Raw intake, before this service decides what it means."""

    external_id: str
    rfc_message_id: str
    subject: str
    sender: str
    recipient: str
    body_html: str
    body_text: str
    received_at: str
    headers: dict[str, str]


class IMailboxClient(ABC):
    """The intake spool that captures inbound SMTP before we own it."""

    @abstractmethod
    def capture(self, limit: int = 200) -> list[CapturedMessage]:
        """Everything currently sitting in the spool."""

    @abstractmethod
    def purge(self, external_ids: list[str]) -> None:
        """Drop messages we have taken ownership of."""

    @abstractmethod
    def reachable(self) -> bool:
        """Whether the spool is up, for diagnostics."""
