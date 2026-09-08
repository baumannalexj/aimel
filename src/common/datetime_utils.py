"""ISO-8601 conversion. Plain functions — utils do not need to be classes.

SQLite has no datetime type, so every timestamp round-trips through text. Everything above the
repository works with `datetime`; only these two functions know about the string form.
"""

from __future__ import annotations

from datetime import datetime, timezone


def to_iso8601_string(moment: datetime) -> str:
    """Microseconds, so two rows written in the same second still sort deterministically."""
    return moment.isoformat(timespec="microseconds")


def from_iso8601_string(value: str, field: str = "timestamp") -> datetime:
    """Parses what we write and what the schema defaults write, which use a `Z` suffix.

    A naive value is assumed to be UTC rather than left naive, otherwise comparing it against an
    aware datetime raises at some unrelated call site later.
    """
    if not value:
        raise ValueError(f"{field} is empty in a row that must have it")
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def parse_or_now(value: str) -> datetime:
    """For intake, where an upstream date may be missing or malformed."""
    try:
        return from_iso8601_string(value)
    except ValueError:
        return datetime.now(timezone.utc)
