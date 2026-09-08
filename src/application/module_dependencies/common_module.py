from __future__ import annotations

from dataclasses import dataclass

from common import repo_paths
from common.config import NamingConfig, SkillConfig
from common.feature_flag_service import FeatureFlagService
from common.naming import NamingPolicy
from common.session import SessionDetector
from common.session_color import SessionColorPalette
from common.skill_installer import SkillInstaller
from common.thread_renderer import ThreadRenderer


@dataclass(frozen=True)
class CommonModuleConfig:
    naming: NamingConfig
    skill: SkillConfig


class CommonModule:
    """Singletons with no adapter of their own: naming, session lookup, rendering, colour."""

    def __init__(self, config: CommonModuleConfig):
        self._naming_policy = NamingPolicy(config.naming)
        self._session_detector = SessionDetector()
        self._thread_renderer = ThreadRenderer()
        self._session_colors = SessionColorPalette()
        self._skill_installer = SkillInstaller(repo_paths.skill_source(), config.skill.target_dir)
        self._feature_flags = FeatureFlagService.with_defaults()

    def provide_naming_policy(self) -> NamingPolicy:
        return self._naming_policy

    def provide_session_detector(self) -> SessionDetector:
        return self._session_detector

    def provide_thread_renderer(self) -> ThreadRenderer:
        return self._thread_renderer

    def provide_session_colors(self) -> SessionColorPalette:
        return self._session_colors

    def provide_skill_installer(self) -> SkillInstaller:
        return self._skill_installer

    def provide_feature_flags(self) -> FeatureFlagService:
        return self._feature_flags
