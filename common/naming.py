from __future__ import annotations

from common.config import NamingConfig
from domain.message import EmailAddress, SessionId, ThreadSlug

TEMPLATE_VARS = ("service", "user", "domain", "session", "session8", "thread", "title")


def render(template: str, **values: str) -> str:
    filled = {var: "" for var in TEMPLATE_VARS}
    filled.update({key: value for key, value in values.items() if value is not None})
    try:
        return template.format(**filled)
    except KeyError as exc:
        raise ValueError(
            f"unknown template variable {exc} — available: {', '.join(TEMPLATE_VARS)}"
        ) from exc


def _context(
    naming: NamingConfig, session: SessionId, thread: ThreadSlug | None, title: str
) -> dict[str, str]:
    return {
        "service": naming.service_name,
        "user": naming.user,
        "domain": naming.domain,
        "session": str(session),
        "session8": session.short,
        "thread": str(thread) if thread else "",
        "title": title,
    }


def human_address(naming: NamingConfig, session: SessionId) -> EmailAddress:
    return EmailAddress(render(naming.human_address, **_context(naming, session, None, "")))


def agent_address(naming: NamingConfig, session: SessionId) -> EmailAddress:
    return EmailAddress(render(naming.agent_address, **_context(naming, session, None, "")))


def subject_for(
    naming: NamingConfig, session: SessionId, thread: ThreadSlug, title: str
) -> str:
    return render(naming.subject_template, **_context(naming, session, thread, title))
