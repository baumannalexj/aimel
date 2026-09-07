"""Stable per-session colour. Light tints, never bold, so sessions read as a tag not a shout."""

from __future__ import annotations

import hashlib
import os
import sys

# Paul Tol's qualitative "light" scheme — colourblind-safe and pale by construction.
PALETTE = (
    "#77AADD",
    "#99DDFF",
    "#44BB99",
    "#BBCC33",
    "#AAAA00",
    "#EEDD88",
    "#EE8866",
    "#FFAABB",
    "#DDDDDD",
)


def color_for(session: object) -> str:
    """Hex colour for a session, stable across runs and machines."""
    digest = hashlib.sha256(str(session).encode()).hexdigest()
    return PALETTE[int(digest, 16) % len(PALETTE)]


def rgb_for(session: object) -> tuple[int, int, int]:
    value = color_for(session).lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("AIMEL_COLOR") == "always":
        return True
    return sys.stdout.isatty()


def paint(session: object, text: str) -> str:
    if not enabled():
        return text
    red, green, blue = rgb_for(session)
    return f"\x1b[38;2;{red};{green};{blue}m{text}\x1b[0m"


def paint_subject(session: object, subject: str) -> str:
    """Colour only the session prefix, leaving the human-written title plain."""
    prefix = str(session)[:8]
    if subject.startswith(prefix):
        return paint(session, prefix) + subject[len(prefix) :]
    return subject
