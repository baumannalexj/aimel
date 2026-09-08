"""Header names in one place.

The transport writes our custom mail headers and the intake client reads them back. They used to
derive the prefix independently, which is a silent-drift bug waiting to happen: rename the service
and intake stops recognising its own mail without anything failing loudly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MailHeaders:
    """The `X-<Service>-*` names, derived once from the service name."""

    service_name: str

    @property
    def prefix(self) -> str:
        return f"X-{self.service_name.title()}"

    @property
    def session(self) -> str:
        return f"{self.prefix}-Session"

    @property
    def thread(self) -> str:
        return f"{self.prefix}-Thread"

    @property
    def actor(self) -> str:
        return f"{self.prefix}-Actor"

    # Mailpit turns this into a sidebar filter, so it is its name and not ours.
    tags: str = "X-Tags"

    # Standard names we read off captured mail.
    in_reply_to: str = "In-Reply-To"
    references: str = "References"


class HttpHeaders:
    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"
    LOCATION = "Location"
    HTML_UTF8 = "text/html; charset=utf-8"
    JSON = "application/json"
