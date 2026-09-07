from __future__ import annotations

from datetime import datetime
from typing import Any

from domain.message import (
    Author,
    Correspondence,
    DeletedMessage,
    EmailAddress,
    LiveMessage,
    Message,
    MessageState,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
)
from domain.thread import Thread
from ports.database_client import IDatabaseClient, Row
from ports.email_repository import IEmailRepository

NOW_DEFAULT = "(strftime('%Y-%m-%dT%H:%M:%SZ','now'))"

BASE_DDL = """
    id             TEXT PRIMARY KEY,
    session        TEXT NOT NULL,
    thread         TEXT NOT NULL,
    subject        TEXT NOT NULL,
    sender         TEXT NOT NULL,
    recipient      TEXT NOT NULL,
    author         TEXT NOT NULL,
    rfc_message_id TEXT NOT NULL,
    in_reply_to    TEXT NOT NULL DEFAULT '',
    refs           TEXT NOT NULL DEFAULT '',
    body_html      TEXT NOT NULL DEFAULT '',
    body_text      TEXT NOT NULL DEFAULT '',
    sent_at        TEXT NOT NULL
"""

CREATE_UNREAD = f'CREATE TABLE IF NOT EXISTS unread ({BASE_DDL})'
CREATE_READ = f"""CREATE TABLE IF NOT EXISTS read (
    {BASE_DDL},
    read_at        TEXT NOT NULL DEFAULT {NOW_DEFAULT}
)"""
CREATE_DELETED = f"""CREATE TABLE IF NOT EXISTS deleted (
    {BASE_DDL},
    previous_state TEXT NOT NULL,
    deleted_at     TEXT NOT NULL DEFAULT {NOW_DEFAULT}
)"""

BASE_FIELDS = (
    "id, session, thread, subject, sender, recipient, author, "
    "rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at"
)
BASE_BINDS = (
    ":id, :session, :thread, :subject, :sender, :recipient, :author, "
    ":rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at"
)

INSERT_UNREAD = f"INSERT INTO unread ({BASE_FIELDS}) VALUES ({BASE_BINDS})"
INSERT_READ = f"INSERT INTO read ({BASE_FIELDS}) VALUES ({BASE_BINDS})"
INSERT_DELETED = (
    f"INSERT INTO deleted ({BASE_FIELDS}, previous_state) "
    f"VALUES ({BASE_BINDS}, :previous_state)"
)

DELETE_FROM = {
    MessageState.UNREAD: "DELETE FROM unread WHERE id = :id",
    MessageState.READ: "DELETE FROM read WHERE id = :id",
    MessageState.DELETED: "DELETE FROM deleted WHERE id = :id",
}

SELECT_BY_ID = {
    state: f"SELECT * FROM {state.value} WHERE id = :id LIMIT 1" for state in MessageState
}

SELECT_UNREAD = "SELECT * FROM unread ORDER BY sent_at DESC LIMIT :limit"
SELECT_UNREAD_FOR = (
    "SELECT * FROM unread WHERE recipient = :recipient ORDER BY sent_at DESC LIMIT :limit"
)
SELECT_UNREAD_FOR_THREAD = (
    "SELECT * FROM unread WHERE recipient = :recipient AND thread = :thread "
    "ORDER BY sent_at DESC LIMIT :limit"
)
SELECT_BY_STATE = {
    state: f"SELECT * FROM {state.value} ORDER BY sent_at DESC LIMIT :limit"
    for state in MessageState
}
SELECT_THREAD = {
    state: f"SELECT * FROM {state.value} WHERE session = :session AND thread = :thread"
    for state in MessageState
}
EXISTS_RFC = {
    state: f"SELECT 1 FROM {state.value} WHERE rfc_message_id = :rfc LIMIT 1"
    for state in MessageState
}

SELECT_THREADS = """
SELECT thread, subject, COUNT(*) AS count, MAX(sent_at) AS updated_at
FROM (
    SELECT thread, subject, sent_at FROM unread  WHERE session = :session
    UNION ALL
    SELECT thread, subject, sent_at FROM read    WHERE session = :session
    UNION ALL
    SELECT thread, subject, sent_at FROM deleted WHERE session = :session
)
GROUP BY thread
ORDER BY updated_at DESC
"""


class SqliteEmailRepository(IEmailRepository):
    """Composes SQL for the per-state tables. All execution goes through the client."""

    def __init__(self, database_client: IDatabaseClient):
        self._db = database_client

    def ensure_schema(self) -> None:
        for statement in (CREATE_UNREAD, CREATE_READ, CREATE_DELETED):
            self._db.execute(statement)
        for state in MessageState:
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_thread "
                f"ON {state.value} (session, thread, sent_at DESC)"
            )

    # --- writes ---

    def add(self, message: UnreadMessage) -> UnreadMessage:
        self._db.execute(INSERT_UNREAD, _base_binds(message.content))
        return message

    def mark_read(self, message: UnreadMessage) -> ReadMessage:
        with self._db.transaction() as tx:
            tx.execute(DELETE_FROM[MessageState.UNREAD], {"id": message.content.id})
            tx.execute(INSERT_READ, _base_binds(message.content))
        return self._reload(message.content.id, MessageState.READ)

    def soft_delete(self, message: LiveMessage) -> DeletedMessage:
        binds = _base_binds(message.content) | {"previous_state": message.state.value}
        with self._db.transaction() as tx:
            tx.execute(DELETE_FROM[message.state], {"id": message.content.id})
            tx.execute(INSERT_DELETED, binds)
        return self._reload(message.content.id, MessageState.DELETED)

    def _reload(self, message_id: str, state: MessageState) -> Any:
        rows = self._db.query(SELECT_BY_ID[state], {"id": message_id})
        if not rows:
            raise RuntimeError(f"{message_id} vanished from {state.value} after its transaction")
        return _to_message(rows[0], state)

    # --- reads ---

    def find(self, message_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(SELECT_BY_ID[state], {"id": message_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def list_unread(
        self, recipient: str = "", thread: ThreadSlug | None = None, limit: int = 50
    ) -> list[UnreadMessage]:
        if recipient and thread is not None:
            sql = SELECT_UNREAD_FOR_THREAD
            params = {"recipient": recipient, "thread": str(thread), "limit": limit}
        elif recipient:
            sql, params = SELECT_UNREAD_FOR, {"recipient": recipient, "limit": limit}
        else:
            sql, params = SELECT_UNREAD, {"limit": limit}
        return [_to_message(row, MessageState.UNREAD) for row in self._db.query(sql, params)]

    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        rows = self._db.query(SELECT_BY_STATE[state], {"limit": limit})
        return [_to_message(row, state) for row in rows]

    def exists_by_rfc_id(self, rfc_message_id: str) -> bool:
        for state in MessageState:
            if self._db.query(EXISTS_RFC[state], {"rfc": rfc_message_id}):
                return True
        return False

    def history(self, session: SessionId, thread: ThreadSlug) -> list[Message]:
        messages: list[Message] = []
        params = {"session": str(session), "thread": str(thread)}
        for state in MessageState:
            rows = self._db.query(SELECT_THREAD[state], params)
            messages.extend(_to_message(row, state) for row in rows)
        return sorted(messages, key=lambda m: m.content.sent_at, reverse=True)

    def threads(self, session: SessionId) -> list[Thread]:
        rows = self._db.query(SELECT_THREADS, {"session": str(session)})
        return [
            Thread(
                session=session,
                slug=ThreadSlug(row["thread"]),
                subject=row["subject"],
                message_count=row["count"],
                updated_at=_require(row["updated_at"], "updated_at"),
            )
            for row in rows
        ]


def _base_binds(content: Correspondence) -> dict[str, Any]:
    return {
        "id": content.id,
        "session": str(content.session),
        "thread": str(content.thread),
        "subject": content.subject,
        "sender": str(content.sender),
        "recipient": str(content.recipient),
        "author": content.author.value,
        "rfc_message_id": content.rfc_message_id,
        "in_reply_to": content.in_reply_to,
        "refs": " ".join(content.references),
        "body_html": content.body_html,
        "body_text": content.body_text,
        "sent_at": _iso(content.sent_at),
    }


def _to_message(row: Row, state: MessageState) -> Message:
    content = Correspondence(
        id=row["id"],
        session=SessionId(row["session"]),
        thread=ThreadSlug(row["thread"]),
        subject=row["subject"],
        sender=EmailAddress(row["sender"]),
        recipient=EmailAddress(row["recipient"]),
        author=Author(row["author"]),
        rfc_message_id=row["rfc_message_id"],
        in_reply_to=row["in_reply_to"],
        references=tuple(row["refs"].split()),
        body_html=row["body_html"],
        body_text=row["body_text"],
        sent_at=_require(row["sent_at"], "sent_at"),
    )
    if state is MessageState.UNREAD:
        return UnreadMessage(content=content)
    if state is MessageState.READ:
        return ReadMessage(content=content, read_at=_require(row["read_at"], "read_at"))
    return DeletedMessage(
        content=content,
        deleted_at=_require(row["deleted_at"], "deleted_at"),
        previous_state=MessageState(row["previous_state"]),
    )


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def _require(value: str, field: str) -> datetime:
    if not value:
        raise ValueError(f"{field} is empty in a row that must have it")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))