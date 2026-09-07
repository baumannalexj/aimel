from __future__ import annotations

from datetime import datetime
from typing import Any

from domain.message import (
    Author,
    Correspondence,
    DeletedMessage,
    Email,
    LiveMessage,
    Message,
    MessageState,
    NewCorrespondence,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
)
from domain.thread import Thread
from ports.database_client import IDatabaseClient, Row
from ports.email_repository import IEmailRepository

NOW = "(strftime('%Y-%m-%dT%H:%M:%SZ','now'))"

# SQLite has no uuid() builtin, so compose a v4 from randomblob.
NEW_UUID = (
    "(lower(hex(randomblob(4))||'-'||hex(randomblob(2))||'-4'||substr(hex(randomblob(2)),2)"
    "||'-'||substr('89ab',abs(random())%4+1,1)||substr(hex(randomblob(2)),2)"
    "||'-'||hex(randomblob(6))))"
)

IDENTITY_DDL = f"""
    pk             INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid           TEXT NOT NULL UNIQUE DEFAULT {NEW_UUID},
    created_at     TEXT NOT NULL DEFAULT {NOW}"""

CONTENT_DDL = """
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
    sent_at        TEXT NOT NULL"""

CREATE_TABLE = {
    MessageState.UNREAD: f"CREATE TABLE IF NOT EXISTS unread ({IDENTITY_DDL},{CONTENT_DDL})",
    MessageState.READ: (
        f"CREATE TABLE IF NOT EXISTS read ({IDENTITY_DDL},{CONTENT_DDL},"
        f"\n    read_at        TEXT NOT NULL DEFAULT {NOW})"
    ),
    MessageState.DELETED: (
        f"CREATE TABLE IF NOT EXISTS deleted ({IDENTITY_DDL},{CONTENT_DDL},"
        f"\n    previous_state TEXT NOT NULL,"
        f"\n    deleted_at     TEXT NOT NULL DEFAULT {NOW})"
    ),
}

CONTENT_FIELDS = (
    "session, thread, subject, sender, recipient, author, "
    "rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at"
)
CONTENT_BINDS = (
    ":session, :thread, :subject, :sender, :recipient, :author, "
    ":rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at"
)

# New mail: pk, uuid and created_at all come from the schema.
INSERT_NEW_UNREAD = f"INSERT INTO unread ({CONTENT_FIELDS}) VALUES ({CONTENT_BINDS})"

# A move keeps the original uuid and created_at; only the state timestamp is schema-stamped.
INSERT_MOVED_READ = (
    f"INSERT INTO read (uuid, created_at, {CONTENT_FIELDS}) "
    f"VALUES (:uuid, :created_at, {CONTENT_BINDS})"
)
INSERT_MOVED_DELETED = (
    f"INSERT INTO deleted (uuid, created_at, {CONTENT_FIELDS}, previous_state) "
    f"VALUES (:uuid, :created_at, {CONTENT_BINDS}, :previous_state)"
)

DELETE_BY_UUID = {
    state: f"DELETE FROM {state.value} WHERE uuid = :uuid" for state in MessageState
}
SELECT_BY_UUID = {
    state: f"SELECT * FROM {state.value} WHERE uuid = :uuid LIMIT 1" for state in MessageState
}
SELECT_LAST_INSERTED = "SELECT * FROM unread WHERE pk = last_insert_rowid()"
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

SELECT_UNREAD = "SELECT * FROM unread ORDER BY sent_at DESC LIMIT :limit"
SELECT_UNREAD_FOR = (
    "SELECT * FROM unread WHERE recipient = :recipient ORDER BY sent_at DESC LIMIT :limit"
)
SELECT_UNREAD_FOR_THREAD = (
    "SELECT * FROM unread WHERE recipient = :recipient AND thread = :thread "
    "ORDER BY sent_at DESC LIMIT :limit"
)

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
        for state in MessageState:
            self._db.execute(CREATE_TABLE[state])
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_thread "
                f"ON {state.value} (session, thread, sent_at DESC)"
            )

    # --- writes ---

    def add(self, correspondence: NewCorrespondence) -> UnreadMessage:
        with self._db.transaction() as tx:
            tx.execute(INSERT_NEW_UNREAD, _content_binds(correspondence))
            rows = tx.query(SELECT_LAST_INSERTED)
        if not rows:
            raise RuntimeError("insert into unread reported no row")
        return _to_message(rows[0], MessageState.UNREAD)

    def mark_read(self, message: UnreadMessage) -> ReadMessage:
        with self._db.transaction() as tx:
            tx.execute(DELETE_BY_UUID[MessageState.UNREAD], {"uuid": message.content.id})
            tx.execute(INSERT_MOVED_READ, _move_binds(message.content))
        return self._reload(message.content.id, MessageState.READ)

    def soft_delete(self, message: LiveMessage) -> DeletedMessage:
        binds = _move_binds(message.content) | {"previous_state": message.state.value}
        with self._db.transaction() as tx:
            tx.execute(DELETE_BY_UUID[message.state], {"uuid": message.content.id})
            tx.execute(INSERT_MOVED_DELETED, binds)
        return self._reload(message.content.id, MessageState.DELETED)

    def _reload(self, uuid: str, state: MessageState) -> Any:
        rows = self._db.query(SELECT_BY_UUID[state], {"uuid": uuid})
        if not rows:
            raise RuntimeError(f"{uuid} vanished from {state.value} after its transaction")
        return _to_message(rows[0], state)

    # --- reads ---

    def find(self, message_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(SELECT_BY_UUID[state], {"uuid": message_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def list_unread(
        self, recipient: Email | None = None, thread: ThreadSlug | None = None, limit: int = 50
    ) -> list[UnreadMessage]:
        if recipient is not None and thread is not None:
            sql = SELECT_UNREAD_FOR_THREAD
            params = {
                "recipient": recipient.address,
                "thread": str(thread),
                "limit": limit,
            }
        elif recipient is not None:
            sql = SELECT_UNREAD_FOR
            params = {"recipient": recipient.address, "limit": limit}
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
            messages.extend(
                _to_message(row, state) for row in self._db.query(SELECT_THREAD[state], params)
            )
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


def _content_binds(content: NewCorrespondence | Correspondence) -> dict[str, Any]:
    return {
        "session": str(content.session),
        "thread": str(content.thread),
        "subject": content.subject,
        "sender": content.sender.address,
        "recipient": content.recipient.address,
        "author": content.author.value,
        "rfc_message_id": content.rfc_message_id,
        "in_reply_to": content.in_reply_to,
        "refs": " ".join(content.references),
        "body_html": content.body_html,
        "body_text": content.body_text,
        "sent_at": _iso(content.sent_at),
    }


def _move_binds(content: Correspondence) -> dict[str, Any]:
    return _content_binds(content) | {
        "uuid": content.id,
        "created_at": _iso(content.created_at),
    }


def _to_message(row: Row, state: MessageState) -> Message:
    content = Correspondence(
        id=row["uuid"],
        created_at=_require(row["created_at"], "created_at"),
        session=SessionId(row["session"]),
        thread=ThreadSlug(row["thread"]),
        subject=row["subject"],
        sender=Email(row["sender"]),
        recipient=Email(row["recipient"]),
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
