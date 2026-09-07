from __future__ import annotations

import os
import re
from pathlib import Path

from domain.message import SessionId

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def project_slug(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def detect() -> str:
    """The live session is the transcript being written right now — cwd's project dir first."""
    projects = Path.home() / ".claude" / "projects"
    for root in (projects / project_slug(Path.cwd()), projects):
        if not root.is_dir():
            continue
        pattern = "**/*.jsonl" if root == projects else "*.jsonl"
        logs = [p for p in root.glob(pattern) if UUID_RE.fullmatch(p.stem)]
        if logs:
            return max(logs, key=lambda p: p.stat().st_mtime).stem
    return ""


def resolve(explicit: str = "") -> SessionId:
    value = explicit or os.environ.get("AIMEL_SESSION", "") or detect()
    if not value:
        raise ValueError(
            "no session uuid: pass --session, set AIMEL_SESSION, or run where a Claude "
            "transcript exists under ~/.claude/projects/"
        )
    return SessionId(value)
