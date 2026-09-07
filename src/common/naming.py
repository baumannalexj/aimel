from __future__ import annotations

from common.config import NamingConfig
from domain.message import Email, SessionId, ThreadSlug

TEMPLATE_VARS = ("service", "user", "domain", "session", "session8", "thread", "title")


class NamingPolicy:
    """Turns config templates into addresses and subjects."""

    def __init__(self, config: NamingConfig):
        self._config = config

    def render(self, template: str, **values: str) -> str:
        filled = {var: "" for var in TEMPLATE_VARS}
        filled.update({key: value for key, value in values.items() if value is not None})
        try:
            return template.format(**filled)
        except KeyError as exc:
            raise ValueError(
                f"unknown template variable {exc} — available: {', '.join(TEMPLATE_VARS)}"
            ) from exc

    def human_address(self, session: SessionId) -> Email:
        return Email(self.render(self._config.human_address, **self._context(session)))

    def agent_address(self, session: SessionId) -> Email:
        return Email(self.render(self._config.agent_address, **self._context(session)))

    def subject_for(self, session: SessionId, thread: ThreadSlug, title: str) -> str:
        return self.render(
            self._config.subject_template, **self._context(session, thread=thread, title=title)
        )

    def _context(
        self, session: SessionId, thread: ThreadSlug | None = None, title: str = ""
    ) -> dict[str, str]:
        return {
            "service": self._config.service_name,
            "user": self._config.user,
            "domain": self._config.domain,
            "session": str(session),
            "session8": session.short,
            "thread": str(thread) if thread else "",
            "title": title,
        }
