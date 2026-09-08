"""Header names in one place.

The transport writes our custom mail headers and the intake client reads them back. Keeping the
literal strings here, instead of each side deriving its own, is what stops a silent-drift bug: if
they ever disagreed, intake would stop recognising its own mail without anything failing loudly.
"""

from __future__ import annotations


class MailHeaders:
    SESSION = "X-Aimel-Session"
    THREAD = "X-Aimel-Thread"
    ACTOR = "X-Aimel-Actor"

    # Mailpit turns this into a sidebar filter, so it is its name and not ours.
    TAGS = "X-Tags"

    # Standard names we read off captured mail.
    IN_REPLY_TO = "In-Reply-To"
    REFERENCES = "References"


class HttpHeaders:
    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"
    LOCATION = "Location"
    HTML_UTF8 = "text/html; charset=utf-8"
    JSON = "application/json"
    MARKDOWN = "text/markdown; charset=utf-8"
