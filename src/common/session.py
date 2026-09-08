from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

from domain.message import SessionId

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


class SessionDetector:
    """Infers the live Claude session from transcript files on disk."""

    def __init__(
        self,
        projects_root: Path | None = None,
        environ: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ):
        self._environ = environ if environ is not None else os.environ
        self._projects_root = projects_root or Path.home() / ".claude" / "projects"
        self._cwd = cwd

    @staticmethod
    def project_slug(path: Path) -> str:
        return re.sub(r"[^A-Za-z0-9]", "-", str(path))

    def detect(self) -> str:
        """The live session is the transcript being written right now — cwd's project dir first."""
        cwd = self._cwd or Path.cwd()
        candidates = (self._projects_root / self.project_slug(cwd), self._projects_root)
        for root in candidates:
            if not root.is_dir():
                continue
            pattern = "**/*.jsonl" if root == self._projects_root else "*.jsonl"
            logs = [p for p in root.glob(pattern) if UUID_RE.fullmatch(p.stem)]
            if logs:
                return max(logs, key=lambda p: p.stat().st_mtime).stem
        return ""

    def resolve(self, explicit: str = "") -> SessionId:
        value = explicit or self._environ.get("AIMEL_SESSION", "") or self.detect()
        if not value:
            raise ValueError(
                "no session uuid: pass --session, set AIMEL_SESSION, or run where a Claude "
                "transcript exists under ~/.claude/projects/"
            )
        return SessionId(value)
