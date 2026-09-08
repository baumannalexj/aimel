from __future__ import annotations

import shutil
from pathlib import Path


class SkillInstaller:
    """Copies the agent contract where every Claude session will find it."""

    def __init__(self, source: Path, target_dir: Path):
        self._source = Path(source)
        self._target_dir = Path(target_dir)

    def install(self) -> Path:
        if not self._source.exists():
            raise SystemExit(f"no skill to install at {self._source}")
        self._target_dir.mkdir(parents=True, exist_ok=True)
        target = self._target_dir / self._source.name
        shutil.copyfile(self._source, target)
        return target
