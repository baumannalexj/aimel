from __future__ import annotations

from datetime import datetime
from typing import Any

from domain.message import (
    Author,
    Correspondence,
    DeletedMessage,
    EmailAddress,
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

BASE_COLUMNS = (
    "id",
    "session",
    "thread",
    "subject",
    "sender",
    "recipient",
    "author",
    "rfc_message_id",
    "in_reply_to",
    "refs",
    "body_html",
    "body_text",
    "sent_at",
)

STATE_COLUMNS = {
    MessageState.UNREAD: (),
    MessageState.READ: ("read_at",),
    MessageState.DELETED: ("read_at", "deleted_at"),
}

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


class SqliteEmailRepository(IEmailRepository):
    """Composes SQL for the per-state tables. All execution goes through the client."""

    def __init__(self, database_client: IDatabaseClient):
        self._db = database_client

    def ensure_schema(self) -> None:
        for state, extra in STATE_COLUMNS.items():
            extras = "".join(f",\n    {name} TEXT NOT NULL DEFAULT ''" for name in extra)
            self._db.execute(f'CREATE TABLE IF NOT EXISTS "{state.value}" ({BASE_DDL}{extras})')
            self._db.execute(
                f'CREATE INDEX IF NOT EXISTS "{state.value}_thread" '
                f'ON "{state.value}" (session, thread, sent_at DESC)'
            )

    # --- writes ---

    def add(self, message: UnreadMessage) -> UnreadMessage:
        columns = BASE_COLUMNS
        self._db.execute(
            f'INSERT INTO "unread" ({", ".join(columns)}) '
            f'VALUES ({", ".join(f":{name}" for name in columns)})',
            _to_row(message, columns),
        )
        return message

    def mark_read(self, message: ReadMessage) -> ReadMessage:
        self._move(message)
        return message

    def soft_delete(self, message: DeletedMessage) -> DeletedMessage:
        self._move(message)
        return message

    def _move(self, message: Message) -> None:
        columns = BASE_COLUMNS + STATE_COLUMNS[message.state]
        with self._db.transaction():
            for state in MessageState:
                self._db.execute(
                    f'DELETE FROM "{state.value}" WHERE id = :id', {"id": message.content.id}
                )
            self._db.execute(
                f'INSERT INTO "{message.state.value}" ({", ".join(columns)}) '
                f'VALUES ({", ".join(f":{name}" for name in columns)})',
                _to_row(message, columns),
            )

    # --- reads ---

    def find(self, message_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(
                f'SELECT * FROM "{state.value}" WHERE id = :id LIMIT 1', {"id": message_id}
            )
            if rows:
                return _to_message(rows[0], state)
        return None

    def list_unread(
        self, recipient: str = "", thread: ThreadSlug | None = None, limit: int = 50
    ) -> list[UnreadMessage]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit}
        if recipient:
            clauses.append("recipient = :recipient")
            params["recipient"] = recipient
        if thread is not None:
            clauses.append("thread = :thread")
            params["thread"] = str(thread)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._db.query(
            f'SELECT * FROM "unread" {where} ORDER BY sent_at DESC LIMIT :limit', params
        )
        return [_to_message(row, MessageState.UNREAD) for row in rows]

    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        rows = self._db.query(
            f'SELECT * FROM "{state.value}" ORDER BY sent_at DESC LIMIT :limit', {"limit": limit}
        )
        return [_to_message(row, state) for row in rows]

    def exists_by_rfc_id(self, rfc_message_id: str) -> bool:
        for state in MessageState:
            rows = self._db.query(
                f'SELECT 1 FROM "{state.value}" WHERE rfc_message_id = :rfc LIMIT 1',
                {"rfc": rfc_message_id},
            )
            if rows:
                return True
        return False

    def history(self, session: SessionId, thread: ThreadSlug) -> list[Message]:
        messages: list[Message] = []
        for state in MessageState:
            rows = self._db.query(
                f'SELECT * FROM "{state.value}" WHERE session = :session AND thread = :thread',
                {"session": str(session), "thread": str(thread)},
            )
            messages.extend(_to_message(row, state) for row in rows)
        return sorted(messages, key=lambda m: m.content.sent_at, reverse=True)

    def threads(self, session: SessionId) -> list[Thread]:
        union = " UNION ALL ".join(
            f'SELECT thread, subject, sent_at FROM "{state.value}" WHERE session = :session'
            for state in MessageState
        )
        rows = self._db.query(
            f"SELECT thread, subject, COUNT(*) AS count, MAX(sent_at) AS updated_at "
            f"FROM ({union}) GROUP BY thread ORDER BY updated_at DESC",
            {"session": str(session)},
        )
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


def _to_row(message: Message, columns: tuple[str, ...]) -> dict[str, Any]:
    content = message.content
    values = {
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
        "read_at": _iso(getattr(message, "read_at", None)),
        "deleted_at": _iso(getattr(message, "deleted_at", None)),
    }
    return {name: values[name] for name in columns}


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
        read_at=_parse(row["read_at"]),
    )


def _iso(moment: datetime | None) -> str:
    return moment.isoformat(timespec="seconds") if moment else ""


def _parse(value: str) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _require(value: str, field: str) -> datetime:
    parsed = _parse(value)
    if parsed is None:
        raise ValueError(f"{field} is empty in a row that must have it")
    return parsed
