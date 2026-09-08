from __future__ import annotations

from common.config import NamingConfig, PathsConfig
from common.naming import NamingPolicy
from common.session import SessionDetector
from common.session_color import SessionColorPalette
from common.skill_installer import SkillInstaller
from common.thread_renderer import ThreadRenderer


class CommonModule:
    """Singletons with no adapter of their own: naming, session lookup, rendering, colour."""

    def __init__(self, naming: NamingConfig, paths: PathsConfig):
        self._naming_policy = NamingPolicy(naming)
        self._session_detector = SessionDetector()
        self._thread_renderer = ThreadRenderer()
        self._session_colors = SessionColorPalette()
        self._skill_installer = SkillInstaller(paths.skill_source, paths.skill_target_dir)

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
