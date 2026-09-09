from __future__ import annotations

from common.datetime_utils import parse_or_now
from common.thread_renderer import ThreadRenderer
from domain.commands import (
    EmailDelete,
    EmailReply,
    EmailSendNewThread,
    IncludeHistory,
    SentEmail,
)
from domain.message import (
    Actor,
    DeletedMessage,
    Email,
    EmailSubject,
    HtmlBody,
    Message,
    MessageState,
    ReadMessage,
    SessionId,
    UnreadMessage,
    now,
)
from domain.outgoing import Envelope
from domain.thread import ThreadSummary
from ports.email_repository import IEmailRepository
from ports.email_transport import IEmailTransport
from ports.mailbox_client import CapturedMessage, IMailboxClient

INTAKE_SESSION = "00000000-0000-4000-8000-000000000000"


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

    def send_new_thread(self, command: EmailSendNewThread) -> UnreadMessage:
        envelope = Envelope(
            sender=command.sender,
            recipient=command.recipient,
            subject=command.subject,
            session=command.session,
            actor=command.author,
            in_reply_to="",
            references=(),
        )
        rfc_message_id = self._transport.send(envelope, command.body_html, "")
        return self._repository.add_new_thread(
            SentEmail(
                session=command.session,
                subject=command.subject,
                sender=command.sender,
                recipient=command.recipient,
                author=command.author,
                rfc_message_id=rfc_message_id,
                in_reply_to="",
                references=(),
                body_html=command.body_html,
                body_text=command.body_html.to_plain_text(),
                sent_at=now(),
            )
        )

    def reply(self, command: EmailReply) -> UnreadMessage:
        history = self._repository.history_for_email(command.in_reply_to_email_id)
        if not history:
            raise ValueError(f"nothing to reply to: {command.in_reply_to_email_id}")
        # The opener carries the thread's context; history is newest-first.
        subject = history[-1].content.subject
        chain = tuple(message.content.rfc_message_id for message in reversed(history))
        body_html = command.body_html
        if body_html and command.include_history is IncludeHistory.ALL:
            body_html = body_html.followed_by(self._renderer.render_history(history))
        envelope = Envelope(
            sender=command.sender,
            recipient=command.recipient,
            subject=subject,
            session=command.session,
            actor=command.author,
            in_reply_to=chain[-1],
            references=chain,
        )
        rfc_message_id = self._transport.send(envelope, body_html, "")
        return self._repository.add_reply(
            SentEmail(
                session=command.session,
                subject=subject,
                sender=command.sender,
                recipient=command.recipient,
                author=command.author,
                rfc_message_id=rfc_message_id,
                in_reply_to=chain[-1],
                references=chain,
                body_html=command.body_html,
                body_text=command.body_html.to_plain_text(),
                sent_at=now(),
            ),
            command.in_reply_to_email_id,
        )

    def poll(self, mailbox: Email, limit: int = 50) -> list[UnreadMessage]:
        return self._repository.list_unread(mailbox, limit=limit)

    def read(self, email_id: str) -> ReadMessage:
        message = self._require(email_id)
        if isinstance(message, ReadMessage):
            return message
        if isinstance(message, DeletedMessage):
            raise ValueError(f"email is deleted: {email_id}")
        return self._repository.mark_read(message)

    def delete(self, command: EmailDelete) -> DeletedMessage:
        message = self._require(command.email_id)
        if isinstance(message, DeletedMessage):
            return message
        return self._repository.soft_delete(message)

    def history(self, email_id: str) -> list[Message]:
        return self._repository.history_for_email(email_id)

    def threads(self, session: SessionId) -> list[ThreadSummary]:
        return self._repository.threads(session)

    def all_threads(self, limit: int = 200) -> list[ThreadSummary]:
        """Every agent's threads, so one inbox can span sessions."""
        return self._repository.all_threads(limit=limit)

    def deleted(self, limit: int = 50) -> list[Message]:
        return self._repository.list_by_state(MessageState.DELETED, limit=limit)

    def drain(self, purge: bool = False, limit: int = 200) -> list[UnreadMessage]:
        """Take ownership of the intake spool, threading by In-Reply-To."""
        claimed: list[UnreadMessage] = []
        taken: list[str] = []
        # Oldest first, otherwise a reply is imported before the email it answers
        # and cannot find its thread.
        for captured in reversed(self._mailbox.capture(limit=limit)):
            taken.append(captured.external_id)
            if self._repository.find_by_rfc_id(captured.rfc_message_id) is not None:
                continue
            sent = self._from_capture(captured)
            anchor = (
                self._repository.find_by_rfc_id(captured.headers.get("in_reply_to", ""))
                if captured.headers.get("in_reply_to")
                else None
            )
            if anchor is None:
                claimed.append(self._repository.add_new_thread(sent))
            else:
                claimed.append(self._repository.add_reply(sent, anchor.content.id))
        if purge and taken:
            self._mailbox.purge(taken)
        return claimed

    def _require(self, email_id: str) -> Message:
        message = self._repository.find(email_id)
        if message is None:
            raise ValueError(f"no such email: {email_id}")
        return message

    def _from_capture(self, captured: CapturedMessage) -> SentEmail:
        return SentEmail(
            session=SessionId(captured.headers.get("session", "") or INTAKE_SESSION),
            subject=EmailSubject(captured.subject or "(no subject)"),
            sender=Email(captured.sender),
            recipient=Email(captured.recipient),
            author=_actor_of(captured),
            rfc_message_id=captured.rfc_message_id,
            in_reply_to=captured.headers.get("in_reply_to", ""),
            references=tuple(captured.headers.get("references", "").split()),
            # Mailpit captured the rendered body, history and all; storing that would
            # duplicate the thread into every reply.
            body_html=HtmlBody(captured.body_html).without_quoted_history(),
            body_text=captured.body_text,
            sent_at=parse_or_now(captured.received_at),
        )



def _actor_of(captured: CapturedMessage) -> Actor:
    """Intake trusts the actor header and falls back to the agent when it is absent."""
    try:
        return Actor(captured.headers.get("actor", ""))
    except ValueError:
        return Actor.AI_AGENT
