"""Every Claude Code session on this machine, read straight off the transcripts it already writes.

~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl is the source of truth -- no hook, no
database, nothing to seed. A subagent's own transcript lives one level deeper, under a
`subagents/` directory, with a non-uuid filename (`agent-*.jsonl`); `UUID_RE` on the stem is what
tells the two apart without opening either.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from common.session import UUID_RE

# Kept short: this is a directory-listing label, not the message itself.
CONTEXT_CHAR_LIMIT = 200


@dataclass(frozen=True)
class TranscriptSession:
    session_uuid: str
    project: str
    #: Claude Code's own generated title -- the "Session name" shown by /status. Empty until it has
    #: written one, which is why context is kept as the fallback rather than replaced by this.
    name: str
    context: str
    last_active_at: datetime

    @property
    def label(self) -> str:
        """What to show: the session's own name, falling back to its opening prompt."""
        return self.name or self.context


class SessionDirectory:
    """Scans ~/.claude/projects for every top-level session transcript, most recent first."""

    def __init__(self, projects_root: Path | None = None):
        self._root = projects_root or Path.home() / ".claude" / "projects"

    def list_sessions(self, limit: int | None = None) -> list[TranscriptSession]:
        if not self._root.is_dir():
            return []
        # Recursive so subagent files are seen at all -- UUID_RE then drops them before anything
        # opens a byte of them, which is the difference between this being instant and this
        # reading every subagent transcript on the machine.
        candidates = [p for p in self._root.glob("**/*.jsonl") if UUID_RE.fullmatch(p.stem)]
        candidates.sort(key=_mtime, reverse=True)
        if limit is not None:
            candidates = candidates[:limit]
        return [session for session in (self._read(path) for path in candidates) if session]

    def _read(self, path: Path) -> TranscriptSession | None:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return None
        scanned = _scan(path)
        return TranscriptSession(
            session_uuid=path.stem,
            project=scanned.cwd or _decode_project(path.parent.name),
            name=scanned.name,
            context=scanned.context,
            last_active_at=datetime.fromtimestamp(mtime, tz=timezone.utc),
        )


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _decode_project(slug: str) -> str:
    """Fallback only, and wrong whenever the path contained a dot: the slug replaced both "/" and
    "." with "-", so "alexander.baumann" comes back as "alexander/baumann". Used only when the
    transcript never told us its cwd."""
    return "/" + slug.lstrip("-").replace("-", "/")


@dataclass(frozen=True)
class _Scanned:
    cwd: str
    name: str
    context: str

    @property
    def complete(self) -> bool:
        return bool(self.cwd and self.name and self.context)


def _scan(path: Path) -> _Scanned:
    """Reads only as far as it needs the cwd, the session name and the opening prompt.

    The transcript states its own cwd, so the project path is read rather than reconstructed from
    the directory name -- that encoding cannot distinguish a dot from a slash. It also writes an
    "ai-title" record carrying the name /status displays, which is a far better label than the
    opening prompt. All three usually appear in the first couple of dozen lines and the scan stops
    once it has them, so a 2000-line transcript stays about as cheap to label as a short one. A
    session that has not been titled yet simply keeps the prompt as its label.
    """
    cwd = name = context = ""
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                record = _parsed(line)
                if record is None:
                    continue
                if not cwd:
                    cwd = _string(record.get("cwd"))
                if not name and record.get("type") == "ai-title":
                    name = _string(record.get("aiTitle"))[:CONTEXT_CHAR_LIMIT]
                if not context:
                    text = _user_message_text_from(record)
                    if text is not None:
                        context = text[:CONTEXT_CHAR_LIMIT]
                if cwd and name and context:
                    break
    except OSError:
        pass
    return _Scanned(cwd=cwd, name=name, context=context)


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _parsed(line: str) -> dict | None:
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    return record if isinstance(record, dict) else None


def _user_message_text_from(record: dict) -> str | None:
    if record.get("type") != "user":
        return None
    message = record.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None
