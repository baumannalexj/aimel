from __future__ import annotations

import getpass
import json
import os
from dataclasses import dataclass
from pathlib import Path

SETTINGS_PATH = Path(
    os.environ.get("AIMEL_SETTINGS", Path.home() / ".config" / "aimel" / "settings.json")
)

DEFAULTS: dict[str, object] = {
    "service_name": "aimel",
    "mail_dir": "~/_claude-email",
    "smtp_host": "localhost",
    "smtp_port": 1025,
    "api_base": "http://localhost:8025",
    "domain": "aimel.com",
    "human_address": "{user}@{domain}",
    "agent_address": "claude-{session8}@{domain}",
    "subject_template": "{session8}: {title}",
    "max_messages": 5000,
    "purge_after_drain": False,
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
class AppConfig:
    mail_dir: Path
    database: DatabaseConfig
    smtp: SmtpConfig
    mailbox: MailboxConfig
    naming: NamingConfig
    purge_after_drain: bool


def raw_settings() -> dict[str, object]:
    settings = dict(DEFAULTS)
    if SETTINGS_PATH.exists():
        settings.update(json.loads(SETTINGS_PATH.read_text()))
    for key in DEFAULTS:
        override = os.environ.get("AIMEL_" + key.upper())
        if override is not None:
            settings[key] = override
    return settings


def save_settings(settings: dict[str, object]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")


def load() -> AppConfig:
    settings = raw_settings()
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
            user=_current_user(),
            human_address=str(settings["human_address"]),
            agent_address=str(settings["agent_address"]),
            subject_template=str(settings["subject_template"]),
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
