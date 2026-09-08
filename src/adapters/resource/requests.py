"""Wire shapes. Validated by pydantic at the edge, then turned into domain commands.

One request per operation, so no field is ever meaningless — a reply always names the email it
answers, and opening a thread never carries a thread id.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.commands import EmailDelete, EmailReply, EmailSendNewThread
from domain.message import Author, Email, EmailSubject, SessionId


class _Request(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SendNewThreadRequest(_Request):
    session: str = ""
    title: str = Field(min_length=1)
    html: str = ""
    text: str = ""
    as_human: bool = False

    def to_domain(
        self, session: SessionId, sender: Email, recipient: Email, subject: EmailSubject
    ) -> EmailSendNewThread:
        return EmailSendNewThread(
            session=session,
            subject=subject,
            sender=sender,
            recipient=recipient,
            author=Author.HUMAN if self.as_human else Author.AGENT,
            body_html=self.html,
            body_text=self.text,
        )


class ReplyRequest(_Request):
    session: str = "" # UUID
    email_id: str = Field(min_length=1) # also UUID
    html: str = "" # what's different from html and test? I think you can also change "subject"
    text: str = ""
    as_human: bool = False # try to avoid booleans - use Actor enum like HUMAN | CLAUDE |
    include_history: bool = True # use an enum like IncludeHistory NONE | ALL

    def to_domain(self, session: SessionId, sender: Email, recipient: Email) -> EmailReply:
        return EmailReply(
            session=session,
            in_reply_to_email_id=self.email_id,
            sender=sender,
            recipient=recipient,
            author=Author.HUMAN if self.as_human else Author.AGENT,
            body_html=self.html,
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
    session: str = "" # can this be a UUID
    as_human: bool = False
    limit: int = 50


class SessionScopedRequest(_Request):
    session: str = "" # make uuid


class ListRequest(_Request):
    limit: int = 50


class DrainRequest(_Request):
    purge: bool = False
    limit: int = 200
