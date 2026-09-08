from __future__ import annotations

from datetime import datetime
from typing import Any

from domain.commands import SentEmail
from domain.message import (
    Author,
    Correspondence,
    DeletedMessage,
    Email,
    EmailSubject,
    LiveMessage,
    Message,
    MessageState,
    ReadMessage,
    SessionId,
    UnreadMessage,
)
from domain.thread import ThreadSummary
from ports.database_client import IDatabaseClient, Row
from ports.email_repository import IEmailRepository

NOW = "(strftime('%Y-%m-%dT%H:%M:%SZ','now'))"

# SQLite has no uuid() builtin, so compose a v4 from randomblob.
NEW_UUID = (
    "(lower(hex(randomblob(4))||'-'||hex(randomblob(2))||'-4'||substr(hex(randomblob(2)),2)"
    "||'-'||substr('89ab',abs(random())%4+1,1)||substr(hex(randomblob(2)),2)"
    "||'-'||hex(randomblob(6))))"
)

# uuid is unique because it identifies one email; thread_uuid is not, because a thread has many.
IDENTITY_DDL = f"""
    pk             INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid           TEXT NOT NULL UNIQUE DEFAULT {NEW_UUID},
    thread_uuid    TEXT NOT NULL DEFAULT {NEW_UUID},
    created_at     TEXT NOT NULL DEFAULT {NOW}"""

CONTENT_DDL = """
    session        TEXT NOT NULL,
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
    "session, subject, sender, recipient, author, "
    "rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at"
)
CONTENT_BINDS = (
    ":session, :subject, :sender, :recipient, :author, "
    ":rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at"
)

# New thread: thread_uuid is omitted so the schema default mints one.
INSERT_NEW_THREAD = f"INSERT INTO unread ({CONTENT_FIELDS}) VALUES ({CONTENT_BINDS})"
# Reply: the thread uuid is looked up from the answered email and bound explicitly.
INSERT_REPLY = (
    f"INSERT INTO unread (thread_uuid, {CONTENT_FIELDS}) "
    f"VALUES (:thread_uuid, {CONTENT_BINDS})"
)
INSERT_MOVED_READ = (
    f"INSERT INTO read (uuid, thread_uuid, created_at, {CONTENT_FIELDS}) "
    f"VALUES (:uuid, :thread_uuid, :created_at, {CONTENT_BINDS})"
)
INSERT_MOVED_DELETED = (
    f"INSERT INTO deleted (uuid, thread_uuid, created_at, {CONTENT_FIELDS}, previous_state) "
    f"VALUES (:uuid, :thread_uuid, :created_at, {CONTENT_BINDS}, :previous_state)"
)

ALL_EMAILS = (
    "SELECT uuid, thread_uuid FROM unread "
    "UNION ALL SELECT uuid, thread_uuid FROM read "
    "UNION ALL SELECT uuid, thread_uuid FROM deleted"
)
SELECT_THREAD_UUID_BY_EMAIL = f"SELECT thread_uuid FROM ({ALL_EMAILS}) WHERE uuid = :email_id LIMIT 1"

DELETE_BY_UUID = {
    state: f"DELETE FROM {state.value} WHERE uuid = :uuid" for state in MessageState
}
SELECT_BY_UUID = {
    state: f"SELECT * FROM {state.value} WHERE uuid = :uuid LIMIT 1" for state in MessageState
}
SELECT_BY_RFC = {
    state: f"SELECT * FROM {state.value} WHERE rfc_message_id = :rfc LIMIT 1"
    for state in MessageState
}
SELECT_BY_THREAD = {
    state: f"SELECT * FROM {state.value} WHERE thread_uuid = :thread_uuid"
    for state in MessageState
}
SELECT_LAST_INSERTED = "SELECT * FROM unread WHERE pk = last_insert_rowid()"
SELECT_BY_STATE = {
    state: f"SELECT * FROM {state.value} ORDER BY sent_at DESC LIMIT :limit"
    for state in MessageState
}
SELECT_UNREAD_FOR = (
    "SELECT * FROM unread WHERE recipient = :recipient ORDER BY sent_at DESC LIMIT :limit"
)

SELECT_THREADS = """
SELECT thread_uuid,
       subject,
       COUNT(*)      AS count,
       MAX(sent_at)  AS updated_at
FROM (
    SELECT thread_uuid, subject, sent_at FROM unread  WHERE session = :session
    UNION ALL
    SELECT thread_uuid, subject, sent_at FROM read    WHERE session = :session
    UNION ALL
    SELECT thread_uuid, subject, sent_at FROM deleted WHERE session = :session
)
GROUP BY thread_uuid
ORDER BY updated_at DESC
"""

SELECT_LATEST_IN_THREAD = f"""
SELECT uuid FROM (
    SELECT uuid, thread_uuid, sent_at FROM unread
    UNION ALL SELECT uuid, thread_uuid, sent_at FROM read
    UNION ALL SELECT uuid, thread_uuid, sent_at FROM deleted
) WHERE thread_uuid = :thread_uuid ORDER BY sent_at DESC LIMIT 1
"""


class SqliteEmailRepository(IEmailRepository):
    """Composes SQL for the per-state tables. All execution goes through the client."""

    def __init__(self, database_client: IDatabaseClient):
        self._db = database_client

    def ensure_schema(self) -> None:
        for state in MessageState:
            self._db.execute(CREATE_TABLE[state])
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_thread_uuid "
                f"ON {state.value} (thread_uuid, sent_at DESC)"
            )
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_session "
                f"ON {state.value} (session, sent_at DESC)"
            )

    # --- writes ---

    def add_new_thread(self, sent: SentEmail) -> UnreadMessage:
        with self._db.transaction() as tx:
            tx.execute(INSERT_NEW_THREAD, _content_binds(sent))
            rows = tx.query(SELECT_LAST_INSERTED)
        if not rows:
            raise RuntimeError("insert into unread reported no row")
        return _to_message(rows[0], MessageState.UNREAD)

    def add_reply(self, sent: SentEmail, in_reply_to_email_id: str) -> UnreadMessage:
        thread_uuid = self._thread_uuid_of(in_reply_to_email_id)
        binds = _content_binds(sent) | {"thread_uuid": thread_uuid}
        with self._db.transaction() as tx:
            tx.execute(INSERT_REPLY, binds)
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

    def _thread_uuid_of(self, email_id: str) -> str:
        rows = self._db.query(SELECT_THREAD_UUID_BY_EMAIL, {"email_id": email_id})
        if not rows:
            raise ValueError(f"cannot reply to an email that does not exist: {email_id}")
        return rows[0]["thread_uuid"]

    def _reload(self, uuid: str, state: MessageState) -> Any:
        rows = self._db.query(SELECT_BY_UUID[state], {"uuid": uuid})
        if not rows:
            raise RuntimeError(f"{uuid} vanished from {state.value} after its transaction")
        return _to_message(rows[0], state)

    # --- reads ---

    def find(self, email_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(SELECT_BY_UUID[state], {"uuid": email_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def find_by_rfc_id(self, rfc_message_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(SELECT_BY_RFC[state], {"rfc": rfc_message_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def list_unread(self, recipient: Email, limit: int = 50) -> list[UnreadMessage]:
        rows = self._db.query(
            SELECT_UNREAD_FOR, {"recipient": recipient.address, "limit": limit}
        )
        return [_to_message(row, MessageState.UNREAD) for row in rows]

    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        rows = self._db.query(SELECT_BY_STATE[state], {"limit": limit})
        return [_to_message(row, state) for row in rows]

    def history_for_email(self, email_id: str) -> list[Message]:
        thread_uuid = self._thread_uuid_of(email_id)
        messages: list[Message] = []
        for state in MessageState:
            messages.extend(
                _to_message(row, state)
                for row in self._db.query(SELECT_BY_THREAD[state], {"thread_uuid": thread_uuid})
            )
        return sorted(messages, key=lambda m: m.content.sent_at, reverse=True)

    def threads(self, session: SessionId) -> list[ThreadSummary]:
        summaries = []
        for row in self._db.query(SELECT_THREADS, {"session": str(session)}):
            latest = self._db.query(
                SELECT_LATEST_IN_THREAD, {"thread_uuid": row["thread_uuid"]}
            )
            summaries.append(
                ThreadSummary(
                    session=session,
                    thread_uuid=row["thread_uuid"],
                    subject=EmailSubject(row["subject"]),
                    message_count=row["count"],
                    latest_email_id=latest[0]["uuid"] if latest else "",
                    updated_at=_require(row["updated_at"], "updated_at"),
                )
            )
        return summaries


def _content_binds(sent: SentEmail | Correspondence) -> dict[str, Any]:
    return {
        "session": str(sent.session),
        "subject": sent.subject.text,
        "sender": sent.sender.address,
        "recipient": sent.recipient.address,
        "author": sent.author.value,
        "rfc_message_id": sent.rfc_message_id,
        "in_reply_to": sent.in_reply_to,
        "refs": " ".join(sent.references),
        "body_html": sent.body_html,
        "body_text": sent.body_text,
        "sent_at": _iso(sent.sent_at),
    }


def _move_binds(content: Correspondence) -> dict[str, Any]:
    return _content_binds(content) | {
        "uuid": content.id,
        "thread_uuid": content.thread_uuid,
        "created_at": _iso(content.created_at),
    }


def _to_message(row: Row, state: MessageState) -> Message:
    content = Correspondence(
        id=row["uuid"],
        created_at=_require(row["created_at"], "created_at"),
        thread_uuid=row["thread_uuid"],
        session=SessionId(row["session"]),
        subject=EmailSubject(row["subject"]),
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
    """Microseconds, so two emails in the same second still sort deterministically."""
    return moment.isoformat(timespec="microseconds")


def _require(value: str, field: str) -> datetime:
    if not value:
        raise ValueError(f"{field} is empty in a row that must have it")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
