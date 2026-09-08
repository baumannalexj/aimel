from __future__ import annotations

import getpass
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULTS: dict[str, object] = {
    "service_name": "aimel",
    "mail_dir": "~/_claude-email",
    "smtp_host": "localhost",
    "smtp_port": 1025,
    "api_base": "http://localhost:8025",
    "domain": "aimel.com",
    "human_address": "{user}@{domain}",
    "agent_address": "claude-{session8}@{domain}",
    "subject_template": "{title}",
    "max_messages": 5000,
    "purge_after_drain": False,
    "skill_target_dir": "~/.claude/skills/aimel",
}


@dataclass(frozen=True)
class DatabaseConfig:
    path: Path
    timeout_seconds: float


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    service_name: str


@dataclass(frozen=True)
class MailboxConfig:
    api_base: str


@dataclass(frozen=True)
class NamingConfig:
    service_name: str
    domain: str
    user: str
    human_address: str
    agent_address: str
    subject_template: str


@dataclass(frozen=True)
class PathsConfig:
    compose_file: Path
    skill_source: Path
    skill_target_dir: Path


@dataclass(frozen=True)
class AppConfig:
    mail_dir: Path
    database: DatabaseConfig
    smtp: SmtpConfig
    mailbox: MailboxConfig
    naming: NamingConfig
    paths: PathsConfig
    purge_after_drain: bool


class ConfigLoader:
    """Reads and writes the settings file. Paths and environment are injected for testability."""

    def __init__(
        self,
        settings_path: Path | None = None,
        environ: Mapping[str, str] | None = None,
        user: str | None = None,
    ):
        self._environ = environ if environ is not None else os.environ
        self._settings_path = settings_path or Path(
            self._environ.get(
                "AIMEL_SETTINGS", str(Path.home() / ".config" / "aimel" / "settings.json")
            )
        )
        self._user = user or _current_user()

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    def raw(self) -> dict[str, object]:
        settings = dict(DEFAULTS)
        if self._settings_path.exists():
            settings.update(json.loads(self._settings_path.read_text()))
        for key in DEFAULTS:
            override = self._environ.get("AIMEL_" + key.upper())
            if override is not None:
                settings[key] = override
        return settings

    def save(self, settings: dict[str, object]) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")

    def load(self) -> AppConfig:
        settings = self.raw()
        mail_dir = Path(str(settings["mail_dir"])).expanduser()
        service_name = str(settings["service_name"])
        return AppConfig(
            mail_dir=mail_dir,
            database=DatabaseConfig(path=mail_dir / "inbox" / "mail.db", timeout_seconds=5.0),
            smtp=SmtpConfig(
                host=str(settings["smtp_host"]),
                port=int(str(settings["smtp_port"])),
                service_name=service_name,
            ),
            mailbox=MailboxConfig(api_base=str(settings["api_base"])),
            naming=NamingConfig(
                service_name=service_name,
                domain=str(settings["domain"]),
                user=self._user,
                human_address=str(settings["human_address"]),
                agent_address=str(settings["agent_address"]),
                subject_template=str(settings["subject_template"]),
            ),
            paths=PathsConfig(
                compose_file=_repo_root() / "compose.yml",
                skill_source=_repo_root() / "skill" / "SKILL.md",
                skill_target_dir=Path(str(settings["skill_target_dir"])).expanduser(),
            ),
            purge_after_drain=_as_bool(settings["purge_after_drain"]),
        )


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "human")


def _repo_root() -> Path:
    """src/common/config.py -> repo root. Overridable for an installed copy."""
    override = os.environ.get("AIMEL_REPO_ROOT")
    return Path(override).expanduser() if override else Path(__file__).resolve().parents[2]
