"""Serves the agent contract: a listing, and the markdown itself."""

from __future__ import annotations

from adapters.resource.api_responses import SkillListItem
from common.skill_catalog import SkillCatalog


class SkillResource:
    def __init__(self, catalog: SkillCatalog):
        self._catalog = catalog

    def skills(self) -> list[SkillListItem]:
        return [SkillListItem.of(skill) for skill in self._catalog.all()]

    def markdown(self, name: str) -> str | None:
        """None for an unknown name, so the caller decides the status code."""
        skill = self._catalog.find(name)
        return skill.markdown if skill else None
