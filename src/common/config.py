from __future__ import annotations

import getpass
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from common import repo_paths

# --- JSON marshalling models ---
#
# These mirror config.json / config.local.json exactly, key for key. They exist only to turn the
# file into typed values; the rest of the app never sees them, it sees the dataclasses below.


class _SmtpSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str
    port: int


class _DatabaseSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    timeout_seconds: float = Field(alias="timeoutSeconds")


class _NamingSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    service_name: str = Field(alias="serviceName")
    domain: str
    human_address: str = Field(alias="humanAddress")
    agent_address: str = Field(alias="agentAddress")
    subject_template: str = Field(alias="subjectTemplate")


class DefaultPortOwner(Enum):
    """Which app answers on the default port. SPOOL is the long-standing experience."""

    SPOOL = "spool"
    REPLY = "reply"


class _WebSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_port_owner: DefaultPortOwner = Field(alias="defaultPortOwner")
    default_port: int = Field(alias="defaultPort")
    spool_alternate_port: int = Field(alias="spoolAlternatePort")
    reply_alternate_port: int = Field(alias="replyAlternatePort")


class _SkillSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_dir: str = Field(alias="targetDir")


class AppSettings(BaseModel):
    """The full shape of config.json / config.local.json / settings.json, once merged."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    mail_dir: str = Field(alias="mailDir")
    purge_after_drain: bool = Field(alias="purgeAfterDrain")
    smtp_config: _SmtpSettings = Field(alias="smtpConfig")
    database_config: _DatabaseSettings = Field(alias="databaseConfig")
    naming_config: _NamingSettings = Field(alias="namingConfig")
    web_config: _WebSettings = Field(alias="webConfig")
    skill_config: _SkillSettings = Field(alias="skillConfig")


# --- runtime config, as the rest of the app sees it ---


@dataclass(frozen=True)
class DatabaseConfig:
    path: Path
    timeout_seconds: float


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int


@dataclass(frozen=True)
class WebConfig:
    default_port_owner: DefaultPortOwner
    spool_port: int
    reply_port: int

    @property
    def api_port(self) -> int:
        """One above the ui, so the pair is predictable from either end."""
        return self.reply_port + 1

    @classmethod
    def of(cls, settings: _WebSettings) -> "WebConfig":
        if settings.default_port_owner is DefaultPortOwner.REPLY:
            return cls(
                settings.default_port_owner,
                spool_port=settings.spool_alternate_port,
                reply_port=settings.default_port,
            )
        return cls(
            settings.default_port_owner,
            spool_port=settings.default_port,
            reply_port=settings.reply_alternate_port,
        )


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
class SkillConfig:
    target_dir: Path


@dataclass(frozen=True)
class AppConfig:
    mail_dir: Path
    database: DatabaseConfig
    smtp: SmtpConfig
    mailbox: MailboxConfig
    naming: NamingConfig
    skill: SkillConfig
    web: WebConfig
    purge_after_drain: bool


# --- environment overrides ---
#
# Every override is named here, literally — never built from the setting's own key — so a setting
# is findable by grepping for the exact env var, not by knowing the naming convention.

_ENV_OVERRIDES: tuple[tuple[str, tuple[str, ...], Callable[[str], object]], ...] = (
    ("AIMEL_MAIL_DIR", ("mailDir",), str),
    ("AIMEL_PURGE_AFTER_DRAIN", ("purgeAfterDrain",), lambda v: _as_bool(v)),
    ("AIMEL_SMTP_HOST", ("smtpConfig", "host"), str),
    ("AIMEL_SMTP_PORT", ("smtpConfig", "port"), int),
    ("AIMEL_DATABASE_TIMEOUT_SECONDS", ("databaseConfig", "timeoutSeconds"), float),
    ("AIMEL_NAMING_SERVICE_NAME", ("namingConfig", "serviceName"), str),
    ("AIMEL_NAMING_DOMAIN", ("namingConfig", "domain"), str),
    ("AIMEL_NAMING_HUMAN_ADDRESS", ("namingConfig", "humanAddress"), str),
    ("AIMEL_NAMING_AGENT_ADDRESS", ("namingConfig", "agentAddress"), str),
    ("AIMEL_NAMING_SUBJECT_TEMPLATE", ("namingConfig", "subjectTemplate"), str),
    ("AIMEL_WEB_DEFAULT_PORT_OWNER", ("webConfig", "defaultPortOwner"), str),
    ("AIMEL_WEB_DEFAULT_PORT", ("webConfig", "defaultPort"), int),
    ("AIMEL_WEB_SPOOL_ALTERNATE_PORT", ("webConfig", "spoolAlternatePort"), int),
    ("AIMEL_WEB_REPLY_ALTERNATE_PORT", ("webConfig", "replyAlternatePort"), int),
    ("AIMEL_SKILL_TARGET_DIR", ("skillConfig", "targetDir"), str),
)


class ConfigLoader:
    """Reads and writes the settings file. Paths and environment are injected for testability.

    Three layers, each optional and merged over the last: the committed config.json, the gitignored
    config.local.json, then the runtime-persisted settings file. Environment variables in
    `_ENV_OVERRIDES` win over all three.
    """

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
        repo_root = repo_paths.repo_root(self._environ)
        settings = _read_json(repo_root / "config.json")
        local_path = repo_root / "config.local.json"
        if local_path.exists():
            settings = _deep_merge(settings, _read_json(local_path))
        if self._settings_path.exists():
            settings = _deep_merge(settings, _read_json(self._settings_path))
        _apply_env_overrides(settings, self._environ)
        return settings

    def save(self, settings: dict[str, object]) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")

    def load(self) -> AppConfig:
        try:
            settings = AppSettings.model_validate(self.raw())
        except ValidationError as exc:
            raise SystemExit(f"invalid configuration: {exc}") from exc
        mail_dir = Path(settings.mail_dir).expanduser()
        web = WebConfig.of(settings.web_config)
        return AppConfig(
            mail_dir=mail_dir,
            database=DatabaseConfig(
                path=mail_dir / "inbox" / "mail.db",
                timeout_seconds=settings.database_config.timeout_seconds,
            ),
            smtp=SmtpConfig(host=settings.smtp_config.host, port=settings.smtp_config.port),
            mailbox=MailboxConfig(api_base=f"http://localhost:{web.spool_port}"),
            naming=NamingConfig(
                service_name=settings.naming_config.service_name,
                domain=settings.naming_config.domain,
                user=self._user,
                human_address=settings.naming_config.human_address,
                agent_address=settings.naming_config.agent_address,
                subject_template=settings.naming_config.subject_template,
            ),
            skill=SkillConfig(target_dir=Path(settings.skill_config.target_dir).expanduser()),
            web=web,
            purge_after_drain=settings.purge_after_drain,
        )


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def _deep_merge(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def _apply_env_overrides(settings: dict[str, object], environ: Mapping[str, str]) -> None:
    for env_var, path, cast in _ENV_OVERRIDES:
        value = environ.get(env_var)
        if value is None:
            continue
        node = settings
        for key in path[:-1]:
            node = node.setdefault(key, {})  # type: ignore[assignment]
        node[path[-1]] = cast(value)  # type: ignore[index]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "human")
