from __future__ import annotations

from abc import ABC, abstractmethod

from domain.outgoing import Envelope


class IEmailTransport(ABC):
    """Puts a message on the wire."""

    @abstractmethod
    def send(self, envelope: Envelope, body_html: str, body_text: str) -> str:
        """Deliver it and return the RFC Message-ID it went out with."""
