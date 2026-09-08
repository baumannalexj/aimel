from __future__ import annotations

from common.config import NamingConfig
from domain.message import Email, EmailSubject, SessionId

_NO_SESSION = "00000000-0000-4000-8000-000000000000"

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

    def mailbox_owner_address(self) -> Email:
        """The human's address for a request that belongs to no session — an inbox listing.

        Raises rather than guessing if the template ever starts varying by session. Passing a
        placeholder session would silently produce the wrong mailbox, and an inbox showing the wrong
        person's mail is worse than an error.
        """
        template = self._config.human_address
        for session_variable in ("{session}", "{session8}"):
            if session_variable in template:
                raise ValueError(
                    f"human_address templates on {session_variable}, so it cannot be resolved "
                    "without a session — give the caller a real one"
                )
        return Email(self.render(template, **self._context(SessionId(_NO_SESSION))))

    def human_address(self, session: SessionId) -> Email:
        return Email(self.render(self._config.human_address, **self._context(session)))

    def agent_address(self, session: SessionId) -> Email:
        return Email(self.render(self._config.agent_address, **self._context(session)))

    def subject_for(self, session: SessionId, title: str) -> EmailSubject:
        return EmailSubject(self.render(self._config.subject_template,
                                        **self._context(session, title=title)))

    def _context(self, session: SessionId, title: str = "") -> dict[str, str]:
        return {
            "service": self._config.service_name,
            "user": self._config.user,
            "domain": self._config.domain,
            "session": str(session),
            "session8": session.short,
            "title": title,
        }
