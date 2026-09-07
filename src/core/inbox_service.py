from __future__ import annotations

from datetime import datetime

from common.thread_renderer import ThreadRenderer
from domain.message import (
    Author,
    DeletedMessage,
    Email,
    Message,
    MessageState,
    NewCorrespondence,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
    now,
)
from domain.outgoing import Draft, Envelope
from domain.thread import Thread
from ports.email_repository import IEmailRepository
from ports.email_transport import IEmailTransport
from ports.mailbox_client import CapturedMessage, IMailboxClient


class InboxService:
    """Correspondence logic. Talks only to ports, domain models and injected collaborators."""

    def __init__(
        self,
        email_repository: IEmailRepository,
        email_transport: IEmailTransport,
        mailbox_client: IMailboxClient,
        thread_renderer: ThreadRenderer,
    ):
        self._repository = email_repository
        self._transport = email_transport
        self._mailbox = mailbox_client
        self._renderer = thread_renderer

    def send(self, draft: Draft) -> UnreadMessage:
        history = self._repository.history(draft.session, draft.thread)
        chain = tuple(message.content.rfc_message_id for message in reversed(history))
        envelope = Envelope(
            sender=draft.sender,
            recipient=draft.recipient,
            subject=draft.subject,
            session=draft.session,
            thread=draft.thread,
            in_reply_to=chain[-1] if chain else "",
            references=chain,
        )
        body_html = draft.body_html
        if body_html and draft.include_history and history:
            body_html += self._renderer.render_history(history)
        rfc_message_id = self._transport.send(envelope, body_html, draft.body_text)
        return self._repository.add(
            NewCorrespondence(
                session=draft.session,
                thread=draft.thread,
                subject=draft.subject,
                sender=draft.sender,
                recipient=draft.recipient,
                author=draft.author,
                rfc_message_id=rfc_message_id,
                in_reply_to=envelope.in_reply_to,
                references=chain,
                body_html=draft.body_html,
                body_text=draft.body_text,
                sent_at=now(),
            )
        )

    def poll(
        self, mailbox: Email, thread: ThreadSlug | None = None, limit: int = 50
    ) -> list[UnreadMessage]:
        return self._repository.list_unread(recipient=mailbox, thread=thread, limit=limit)

    def read(self, message_id: str) -> ReadMessage:
        message = self._require(message_id)
        if isinstance(message, ReadMessage):
            return message
        if isinstance(message, DeletedMessage):
            raise ValueError(f"message is deleted: {message_id}")
        return self._repository.mark_read(message)

    def delete(self, message_id: str) -> DeletedMessage:
        message = self._require(message_id)
        if isinstance(message, DeletedMessage):
            return message
        return self._repository.soft_delete(message)

    def history(self, session: SessionId, thread: ThreadSlug) -> list[Message]:
        return self._repository.history(session, thread)

    def threads(self, session: SessionId) -> list[Thread]:
        return self._repository.threads(session)

    def deleted(self, limit: int = 50) -> list[Message]:
        return self._repository.list_by_state(MessageState.DELETED, limit=limit)

    def drain(self, purge: bool = False, limit: int = 200) -> list[UnreadMessage]:
        """Take ownership of whatever the intake spool captured."""
        claimed: list[UnreadMessage] = []
        taken: list[str] = []
        for captured in self._mailbox.capture(limit=limit):
            taken.append(captured.external_id)
            if self._repository.exists_by_rfc_id(captured.rfc_message_id):
                continue
            claimed.append(self._repository.add(self._from_capture(captured)))
        if purge and taken:
            self._mailbox.purge(taken)
        return claimed

    def _require(self, message_id: str) -> Message:
        message = self._repository.find(message_id)
        if message is None:
            raise ValueError(f"no such message: {message_id}")
        return message

    def _from_capture(self, captured: CapturedMessage) -> NewCorrespondence:
        author = Author.HUMAN if captured.headers.get("author") == "human" else Author.AGENT
        return NewCorrespondence(
            session=SessionId(captured.headers.get("session", "") or "00000000-intake"),
            thread=ThreadSlug(captured.headers.get("thread", "") or "intake"),
            subject=captured.subject,
            sender=Email(captured.sender),
            recipient=Email(captured.recipient),
            author=author,
            rfc_message_id=captured.rfc_message_id,
            in_reply_to=captured.headers.get("in_reply_to", ""),
            references=tuple(captured.headers.get("references", "").split()),
            body_html=captured.body_html,
            body_text=captured.body_text,
            sent_at=_captured_at(captured.received_at),
        )


def _captured_at(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return now()
