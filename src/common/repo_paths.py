"""Where things live on disk relative to the checkout. This is repo layout, not configuration —
it doesn't change between environments, so it has no business in a *Config model.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def repo_root(environ: Mapping[str, str] | None = None) -> Path:
    """src/common/repo_paths.py -> repo root. Overridable for an installed copy, or a test."""
    source = environ if environ is not None else os.environ
    override = source.get("AIMEL_REPO_ROOT")
    return Path(override).expanduser() if override else Path(__file__).resolve().parents[2]


def compose_file() -> Path:
    return repo_root() / "compose.yml"


def skill_source() -> Path:
    return repo_root() / "skill" / "SKILL.md"
