"""Wire shapes. Validated by pydantic at the edge, then turned into domain commands.

One request per operation, so no field is ever meaningless — a reply always names the email it
answers, and opening a thread never carries a thread id.

`html` is the body that renders in the viewer; `text` is only the plain-text alternative part for a
client that cannot render HTML, and is derived from `html` when omitted. The subject is deliberately
not settable on a reply: it is the thread's context, fixed when the thread opens.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.commands import EmailDelete, EmailReply, EmailSendNewThread, IncludeHistory
from domain.message import Actor, Email, EmailSubject, HtmlBody, SessionId


class _Request(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SendNewThreadRequest(_Request):
    session: str = ""  # session uuid; empty means "detect it"
    title: str = Field(min_length=1)  # becomes the subject, set once
    html: str = ""
    text: str = ""
    actor: Actor = Actor.AI_AGENT

    def to_domain(
        self, session: SessionId, sender: Email, recipient: Email, subject: EmailSubject
    ) -> EmailSendNewThread:
        return EmailSendNewThread(
            session=session,
            subject=subject,
            sender=sender,
            recipient=recipient,
            author=self.actor,
            body_html=HtmlBody(self.html),
            body_text=self.text,
        )


class ReplyRequest(_Request):
    session: str = ""  # session uuid
    email_id: str = Field(min_length=1)  # uuid of the email being answered
    html: str = ""
    text: str = ""
    actor: Actor = Actor.AI_AGENT
    include_history: IncludeHistory = IncludeHistory.ALL

    def to_domain(self, session: SessionId, sender: Email, recipient: Email) -> EmailReply:
        return EmailReply(
            session=session,
            in_reply_to_email_id=self.email_id,
            sender=sender,
            recipient=recipient,
            author=self.actor,
            body_html=HtmlBody(self.html),
            body_text=self.text,
            include_history=self.include_history,
        )


class DeleteRequest(_Request):
    email_id: str = Field(min_length=1)

    def to_domain(self) -> EmailDelete:
        return EmailDelete(email_id=self.email_id)


class EmailIdRequest(_Request):
    email_id: str = Field(min_length=1)


class PollRequest(_Request):
    session: str = ""
    mailbox_owner: Actor = Actor.AI_AGENT
    limit: int = 50


class SessionScopedRequest(_Request):
    session: str = ""


class ListRequest(_Request):
    limit: int = 50


class DrainRequest(_Request):
    purge: bool = False
    limit: int = 200
