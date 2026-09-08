"""JSON contract for the web client. camelCase, because the consumer is TypeScript."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from common.session_color import SessionColorPalette
from domain.message import Message
from domain.thread import ThreadSummary

COLORS = SessionColorPalette()


class _Payload(BaseModel):
    model_config = ConfigDict(frozen=True)


class ThreadListItem(_Payload):
    threadUuid: str
    subject: str
    emailCount: int
    unreadCount: int
    latestEmailUuid: str
    session: str
    sessionShort: str
    sessionColor: str
    updatedAt: str

    @classmethod
    def of(cls, thread: ThreadSummary) -> "ThreadListItem":
        return cls(
            threadUuid=thread.thread_uuid,
            subject=thread.subject.text,
            emailCount=thread.message_count,
            unreadCount=thread.unread_count,
            latestEmailUuid=thread.latest_email_id,
            session=str(thread.session),
            sessionShort=thread.session.short,
            sessionColor=COLORS.color_for(thread.session),
            updatedAt=thread.updated_at.isoformat(timespec="seconds"),
        )


class EmailItem(_Payload):
    emailUuid: str
    author: str
    state: str
    sentAt: str
    sender: str
    recipient: str
    bodyHtml: str
    preview: str

    @classmethod
    def of(cls, message: Message) -> "EmailItem":
        content = message.content
        return cls(
            emailUuid=content.id,
            author=content.author.value,
            state=message.state.value,
            sentAt=content.sent_at.isoformat(timespec="seconds"),
            sender=content.sender.address,
            recipient=content.recipient.address,
            bodyHtml=content.body_html.markup,
            preview=content.preview,
        )


class ThreadDetail(_Payload):
    threadUuid: str
    subject: str
    session: str
    sessionShort: str
    sessionColor: str
    emails: list[EmailItem]

    @classmethod
    def of(cls, messages: list[Message]) -> "ThreadDetail":
        """`messages` arrives newest-first; the oldest carries the thread's subject."""
        opener = messages[-1].content
        return cls(
            threadUuid=opener.thread_uuid,
            subject=opener.subject.text,
            session=str(opener.session),
            sessionShort=opener.session.short,
            sessionColor=COLORS.color_for(opener.session),
            emails=[EmailItem.of(message) for message in messages],
        )


class ReplyAccepted(_Payload):
    emailUuid: str
    threadUuid: str

    @classmethod
    def of(cls, message: Message) -> "ReplyAccepted":
        return cls(emailUuid=message.content.id, threadUuid=message.content.thread_uuid)
