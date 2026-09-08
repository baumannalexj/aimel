from __future__ import annotations

from typing import Any

from adapters.repository.sql import email_sql as sql
from common.datetime_utils import from_iso8601_string, to_iso8601_string
from domain.commands import SentEmail
from domain.message import (
    Actor,
    Correspondence,
    DeletedMessage,
    Email,
    EmailSubject,
    HtmlBody,
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


class SqliteEmailRepository(IEmailRepository):
    """Chooses statements and marshals rows. The SQL itself lives in sql/email_sql.py."""

    def __init__(self, database_client: IDatabaseClient):
        self._db = database_client

    def ensure_schema(self) -> None:
        for state in MessageState:
            self._db.execute(sql.CREATE_TABLE[state])
            table = self._db.identifier(state.value)
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_thread_uuid "
                f"ON {table} (thread_uuid, sent_at DESC)"
            )
            self._db.execute(
                f"CREATE INDEX IF NOT EXISTS {state.value}_session "
                f"ON {table} (session, sent_at DESC)"
            )

    # --- writes ---

    def add_new_thread(self, sent: SentEmail) -> UnreadMessage:
        with self._db.transaction() as tx:
            tx.execute(sql.INSERT_NEW_THREAD, _content_binds(sent))
            rows = tx.query(sql.SELECT_LAST_INSERTED)
        return _first(rows, MessageState.UNREAD, "insert into unread reported no row")

    def add_reply(self, sent: SentEmail, in_reply_to_email_id: str) -> UnreadMessage:
        binds = _content_binds(sent) | {
            "thread_uuid": self._thread_uuid_of(in_reply_to_email_id)
        }
        with self._db.transaction() as tx:
            tx.execute(sql.INSERT_REPLY, binds)
            rows = tx.query(sql.SELECT_LAST_INSERTED)
        return _first(rows, MessageState.UNREAD, "insert into unread reported no row")

    def mark_read(self, message: UnreadMessage) -> ReadMessage:
        with self._db.transaction() as tx:
            tx.execute(sql.DELETE_BY_UUID[MessageState.UNREAD], {"uuid": message.content.id})
            tx.execute(sql.INSERT_MOVED_READ, _move_binds(message.content))
        return self._reload(message.content.id, MessageState.READ)

    def soft_delete(self, message: LiveMessage) -> DeletedMessage:
        binds = _move_binds(message.content) | {"previous_state": message.state.value}
        with self._db.transaction() as tx:
            tx.execute(sql.DELETE_BY_UUID[message.state], {"uuid": message.content.id})
            tx.execute(sql.INSERT_MOVED_DELETED, binds)
        return self._reload(message.content.id, MessageState.DELETED)

    def _thread_uuid_of(self, email_id: str) -> str:
        rows = self._db.query(sql.SELECT_THREAD_UUID_BY_EMAIL, {"email_id": email_id})
        if not rows:
            raise ValueError(f"cannot reply to an email that does not exist: {email_id}")
        return rows[0]["thread_uuid"]

    def _reload(self, uuid: str, state: MessageState) -> Any:
        rows = self._db.query(sql.SELECT_BY_UUID[state], {"uuid": uuid})
        return _first(rows, state, f"{uuid} vanished from {state.value} after its transaction")

    # --- reads ---

    def find(self, email_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(sql.SELECT_BY_UUID[state], {"uuid": email_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def find_by_rfc_id(self, rfc_message_id: str) -> Message | None:
        for state in MessageState:
            rows = self._db.query(sql.SELECT_BY_RFC[state], {"rfc": rfc_message_id})
            if rows:
                return _to_message(rows[0], state)
        return None

    def list_unread(self, recipient: Email, limit: int = 50) -> list[UnreadMessage]:
        rows = self._db.query(
            sql.SELECT_UNREAD_FOR_RECIPIENT,
            {"recipient": recipient.address, "limit": limit},
        )
        return [_to_message(row, MessageState.UNREAD) for row in rows]

    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        rows = self._db.query(sql.SELECT_ALL_IN_STATE[state], {"limit": limit})
        return [_to_message(row, state) for row in rows]

    def history_for_email(self, email_id: str) -> list[Message]:
        thread_uuid = self._thread_uuid_of(email_id)
        messages: list[Message] = []
        for state in MessageState:
            rows = self._db.query(sql.SELECT_BY_THREAD[state], {"thread_uuid": thread_uuid})
            messages.extend(_to_message(row, state) for row in rows)
        return sorted(messages, key=lambda m: m.content.sent_at, reverse=True)

    def all_threads(self, limit: int = 200) -> list[ThreadSummary]:
        rows = self._db.query(sql.SELECT_ALL_THREADS, {"limit": limit})
        return [self._summary(SessionId(row["session"]), row) for row in rows]

    def threads(self, session: SessionId) -> list[ThreadSummary]:
        summaries = []
        for row in self._db.query(sql.SELECT_THREADS_FOR_SESSION, {"session": str(session)}):
            latest = self._db.query(
                sql.SELECT_LATEST_EMAIL_IN_THREAD, {"thread_uuid": row["thread_uuid"]}
            )
            summaries.append(self._summary(session, row))
        return summaries

    def _summary(self, session: SessionId, row: Row) -> ThreadSummary:
        latest = self._db.query(
            sql.SELECT_LATEST_EMAIL_IN_THREAD, {"thread_uuid": row["thread_uuid"]}
        )
        return ThreadSummary(
            session=session,
            thread_uuid=row["thread_uuid"],
            subject=EmailSubject(row["subject"]),
            message_count=row["count"],
            latest_email_id=latest[0]["uuid"] if latest else "",
            updated_at=from_iso8601_string(row["updated_at"], "updated_at"),
        )


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
        "body_html": sent.body_html.markup,
        "body_text": sent.body_text,
        "sent_at": to_iso8601_string(sent.sent_at),
    }


def _move_binds(content: Correspondence) -> dict[str, Any]:
    return _content_binds(content) | {
        "uuid": content.id,
        "thread_uuid": content.thread_uuid,
        "created_at": to_iso8601_string(content.created_at),
    }


def _first(rows: list[Row], state: MessageState, complaint: str) -> Any:
    if not rows:
        raise RuntimeError(complaint)
    return _to_message(rows[0], state)


def _to_message(row: Row, state: MessageState) -> Message:
    content = Correspondence(
        id=row["uuid"],
        created_at=from_iso8601_string(row["created_at"], "created_at"),
        thread_uuid=row["thread_uuid"],
        session=SessionId(row["session"]),
        subject=EmailSubject(row["subject"]),
        sender=Email(row["sender"]),
        recipient=Email(row["recipient"]),
        author=Actor(row["author"]),
        rfc_message_id=row["rfc_message_id"],
        in_reply_to=row["in_reply_to"],
        references=tuple(row["refs"].split()),
        body_html=HtmlBody(row["body_html"]),
        body_text=row["body_text"],
        sent_at=from_iso8601_string(row["sent_at"], "sent_at"),
    )
    if state is MessageState.UNREAD:
        return UnreadMessage(content=content)
    if state is MessageState.READ:
        return ReadMessage(
            content=content, read_at=from_iso8601_string(row["read_at"], "read_at")
        )
    return DeletedMessage(
        content=content,
        deleted_at=from_iso8601_string(row["deleted_at"], "deleted_at"),
        previous_state=MessageState(row["previous_state"]),
    )
