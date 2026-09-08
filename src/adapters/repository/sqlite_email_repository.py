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
        self._db.execute(sql.CREATE_THREADS_TABLE)
        self._db.execute(sql.CREATE_EMAILS_TABLE)
        self._db.execute(sql.CREATE_UNREAD_TABLE)
        self._db.execute(sql.CREATE_READ_TABLE)
        self._db.execute(sql.CREATE_DELETED_TABLE)
        self._db.execute(sql.CREATE_INDEX_EMAILS_SESSION)
        self._db.execute(sql.CREATE_INDEX_EMAILS_THREAD)

    # --- writes ---

    def add_new_thread(self, sent: SentEmail) -> UnreadMessage:
        with self._db.transaction() as tx:
            tx.execute(sql.INSERT_THREAD, {"subject": sent.subject.text})
            tx.execute(sql.INSERT_EMAIL_FOR_NEW_THREAD, _content_binds(sent))
            tx.execute(sql.INSERT_UNREAD)
            rows = tx.query(sql.SELECT_LAST_INSERTED)
        return _first(rows, "insert into unread reported no row")

    def add_reply(self, sent: SentEmail, in_reply_to_email_id: str) -> UnreadMessage:
        binds = _content_binds(sent) | {"thread_id": self._thread_id_of(in_reply_to_email_id)}
        with self._db.transaction() as tx:
            tx.execute(sql.INSERT_EMAIL_FOR_REPLY, binds)
            tx.execute(sql.INSERT_UNREAD)
            rows = tx.query(sql.SELECT_LAST_INSERTED)
        return _first(rows, "insert into unread reported no row")

    def mark_read(self, message: UnreadMessage) -> ReadMessage:
        with self._db.transaction() as tx:
            tx.execute(sql.DELETE_BY_UUID[MessageState.UNREAD], {"uuid": message.content.id})
            tx.execute(sql.INSERT_READ, {"uuid": message.content.id})
        return self._reload(message.content.id)

    def soft_delete(self, message: LiveMessage) -> DeletedMessage:
        with self._db.transaction() as tx:
            tx.execute(sql.DELETE_BY_UUID[message.state], {"uuid": message.content.id})
            tx.execute(
                sql.INSERT_DELETED,
                {"uuid": message.content.id, "previous_state": message.state.value},
            )
        return self._reload(message.content.id)

    def _thread_id_of(self, email_id: str) -> int:
        rows = self._db.query(sql.SELECT_THREAD_ID_BY_EMAIL_UUID, {"uuid": email_id})
        if not rows:
            raise ValueError(f"cannot reply to an email that does not exist: {email_id}")
        return rows[0]["thread_id"]

    def _reload(self, uuid: str) -> Any:
        rows = self._db.query(sql.SELECT_BY_UUID, {"uuid": uuid})
        return _first(rows, f"{uuid} vanished after its transaction")

    # --- reads ---

    def find(self, email_id: str) -> Message | None:
        rows = self._db.query(sql.SELECT_BY_UUID, {"uuid": email_id})
        return _to_message(rows[0]) if rows else None

    def find_by_rfc_id(self, rfc_message_id: str) -> Message | None:
        rows = self._db.query(sql.SELECT_BY_RFC, {"rfc": rfc_message_id})
        return _to_message(rows[0]) if rows else None

    def list_unread(self, recipient: Email, limit: int = 50) -> list[UnreadMessage]:
        rows = self._db.query(
            sql.SELECT_UNREAD_FOR_RECIPIENT,
            {"recipient": recipient.address, "limit": limit},
        )
        return [_to_message(row) for row in rows]

    def list_by_state(self, state: MessageState, limit: int = 50) -> list[Message]:
        rows = self._db.query(sql.SELECT_ALL_IN_STATE[state], {"limit": limit})
        return [_to_message(row) for row in rows]

    def history_for_email(self, email_id: str) -> list[Message]:
        thread_id = self._thread_id_of(email_id)
        rows = self._db.query(sql.SELECT_BY_THREAD, {"thread_id": thread_id})
        return [_to_message(row) for row in rows]

    def all_threads(self, limit: int = 200) -> list[ThreadSummary]:
        rows = self._db.query(sql.SELECT_ALL_THREADS, {"limit": limit})
        return [self._summary(SessionId(row["session"]), row) for row in rows]

    def threads(self, session: SessionId) -> list[ThreadSummary]:
        summaries = []
        for row in self._db.query(sql.SELECT_THREADS_FOR_SESSION, {"session": str(session)}):
            latest = self._db.query(
                sql.SELECT_LATEST_EMAIL_IN_THREAD, {"thread_id": row["thread_id"]}
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


def _content_binds(sent: SentEmail) -> dict[str, Any]:
    return {
        "session": str(sent.session),
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


def _first(rows: list[Row], complaint: str) -> Any:
    if not rows:
        raise RuntimeError(complaint)
    return _to_message(rows[0])


def _to_message(row: Row) -> Message:
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
    state = MessageState(row["state"])
    if state is MessageState.UNREAD:
        return UnreadMessage(content=content)
    if state is MessageState.READ:
        return ReadMessage(content=content, read_at=from_iso8601_string(row["read_at"], "read_at"))
    return DeletedMessage(
        content=content,
        deleted_at=from_iso8601_string(row["deleted_at"], "deleted_at"),
        previous_state=MessageState(row["previous_state"]),
    )
