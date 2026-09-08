"""Stable per-session colour. Light tints, never bold, so a session reads as a tag not a shout."""

from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Mapping, Sequence
from typing import TextIO

# Paul Tol's qualitative "light" scheme — colourblind-safe and pale by construction.
TOL_LIGHT = (
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


class SessionColorPalette:
    def __init__(
        self,
        palette: Sequence[str] = TOL_LIGHT,
        environ: Mapping[str, str] | None = None,
        stream: TextIO | None = None,
    ):
        self._palette = tuple(palette)
        self._environ = environ if environ is not None else os.environ
        self._stream = stream

    def color_for(self, session: object) -> str:
        """Hex colour for a session, stable across runs and machines."""
        digest = hashlib.sha256(str(session).encode()).hexdigest()
        return self._palette[int(digest, 16) % len(self._palette)]

    def rgb_for(self, session: object) -> tuple[int, int, int]:
        value = self.color_for(session).lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    def enabled(self) -> bool:
        if self._environ.get("NO_COLOR"):
            return False
        if self._environ.get("AIMEL_COLOR") == "always":
            return True
        stream = self._stream or sys.stdout
        return bool(getattr(stream, "isatty", lambda: False)())

    def paint(self, session: object, text: str) -> str:
        if not self.enabled():
            return text
        red, green, blue = self.rgb_for(session)
        return f"\x1b[38;2;{red};{green};{blue}m{text}\x1b[0m"

    def paint_subject(self, session: object, subject: str) -> str:
        """Colour only the session prefix, leaving the human-written title plain."""
        prefix = str(session)[:8]
        if subject.startswith(prefix):
            return self.paint(session, prefix) + subject[len(prefix) :]
        return subject
