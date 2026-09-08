from __future__ import annotations

from adapters.repository.sql import session_sql as sql
from common.datetime_utils import from_iso8601_string
from domain.message import SessionId
from domain.session import AgentSession
from ports.database_client import IDatabaseClient, Row
from ports.session_repository import ISessionRepository


class SqliteSessionRepository(ISessionRepository):
    """Chooses statements and marshals rows. The SQL itself lives in sql/session_sql.py."""

    def __init__(self, database_client: IDatabaseClient):
        self._db = database_client

    def ensure_schema(self) -> None:
        self._db.execute(sql.CREATE_TABLE)

    def register(self, session_id: SessionId) -> AgentSession:
        self._db.execute(sql.REGISTER, {"session_id": str(session_id)})
        rows = self._db.query(sql.SELECT_BY_SESSION_ID, {"session_id": str(session_id)})
        if not rows:
            raise RuntimeError(f"{session_id} vanished from sessions right after registering")
        return _to_session(rows[0])

    def find(self, session_id: SessionId) -> AgentSession | None:
        rows = self._db.query(sql.SELECT_BY_SESSION_ID, {"session_id": str(session_id)})
        return _to_session(rows[0]) if rows else None

    def list_all(self) -> list[AgentSession]:
        return [_to_session(row) for row in self._db.query(sql.SELECT_ALL)]


def _to_session(row: Row) -> AgentSession:
    return AgentSession(
        id=row["uuid"],
        session_id=SessionId(row["session_id"]),
        created_at=from_iso8601_string(row["created_at"], "created_at"),
        last_seen_at=from_iso8601_string(row["last_seen_at"], "last_seen_at"),
        email_count=row["email_count"],
    )
