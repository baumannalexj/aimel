"""Serves the agent contract over HTTP so a Claude can read it without installing anything.

`aimel install-skill` copies SKILL.md into ~/.claude/skills, which is the right thing for an agent
that lives on this machine. An agent that just wants to know the contract -- or one checking whether
its installed copy has drifted -- should be able to GET it instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from common import repo_paths


@dataclass(frozen=True)
class Skill:
    name: str
    summary: str
    markdown: str
    updated_at: datetime

    @property
    def byte_count(self) -> int:
        """Bytes, not characters. The two differ the moment the contract contains an arrow."""
        return len(self.markdown.encode("utf-8"))


class SkillCatalog:
    """Reads the skill markdown off disk on every call, so an edit needs no restart."""

    def __init__(self, skill_directory: Path | None = None):
        self._directory = skill_directory or repo_paths.skill_source().parent

    def all(self) -> list[Skill]:
        if not self._directory.is_dir():
            return []
        found = (self._load(path) for path in sorted(self._directory.glob("*.md")))
        return [skill for skill in found if skill]

    def find(self, name: str) -> Skill | None:
        """None rather than raising: an unknown name is a 404, which is the caller's decision."""
        wanted = name.lower()
        return next((skill for skill in self.all() if skill.name == wanted), None)

    def _load(self, path: Path) -> Skill | None:
        try:
            markdown = path.read_text(encoding="utf-8")
            stat = path.stat()
        except OSError:
            return None
        front = _frontmatter(markdown)
        return Skill(
            # A skill's name is what its frontmatter declares, because that is the name Claude Code
            # loads it under. The filename is SKILL.md, which would make every skill "skill".
            name=(front.get("name") or path.stem).lower(),
            summary=front.get("description") or _first_prose_line(_body(markdown)),
            markdown=markdown,
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )


def _frontmatter(markdown: str) -> dict[str, str]:
    """The leading --- block, parsed shallowly. No yaml dependency for two flat keys."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and not key.startswith(" "):
            fields[key.strip()] = value.strip()
    return fields


def _body(markdown: str) -> str:
    """Everything after the frontmatter block. Filtering delimiter lines is not enough -- the keys
    inside the block are prose-shaped, so a skill with a name but no description reported
    "name: x" as its summary."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :])
    return markdown


def _first_prose_line(markdown: str) -> str:
    """The first line that is not a heading or a fence."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "```")):
            return stripped
    return ""
