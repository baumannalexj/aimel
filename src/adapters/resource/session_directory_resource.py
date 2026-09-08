"""JSON resource for the session directory. Maps the on-disk transcript scan to the wire contract."""

from __future__ import annotations

from adapters.resource.api_responses import SessionListItem
from common.session_directory import SessionDirectory


class SessionDirectoryApiResource:
    def __init__(self, sessions: SessionDirectory):
        self._sessions = sessions

    def sessions(self, limit: int | None = None) -> list[SessionListItem]:
        return [SessionListItem.of(session) for session in self._sessions.list_sessions(limit)]
