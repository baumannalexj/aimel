"""Component props. One frozen dataclass per component, so each declares its own contract.

A renamed or missing field fails where it is constructed, not silently as a blank in the rendered
page — which is what a loose dict plus Jinja's default `Undefined` would give you.

`Markup` marks the values that are already trusted HTML we generated ourselves, so autoescaping
leaves them alone. Everything else is escaped by default.
"""

from __future__ import annotations

from dataclasses import dataclass

from markupsafe import Markup


@dataclass(frozen=True)
class ChipProps:
    label: str
    color: str


@dataclass(frozen=True)
class ThreadRowProps:
    latest_email_id: str
    subject: str
    email_count: int
    updated_at: str
    chip: ChipProps


@dataclass(frozen=True)
class EmailProps:
    css_class: str
    who: str
    sent_at: str
    sender: str
    recipient: str
    body: Markup


@dataclass(frozen=True)
class InboxPageProps:
    title: str
    rows: tuple[ThreadRowProps, ...]


@dataclass(frozen=True)
class ThreadPageProps:
    title: str
    emails: tuple[EmailProps, ...]
    newest_email_id: str
    responding_enabled: bool


@dataclass(frozen=True)
class NoticePageProps:
    title: str
    message: str
