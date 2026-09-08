"""Response shapes, built by static factories so callers never assemble one by hand."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.message import DeletedMessage, Message


class _Response(BaseModel):
    model_config = ConfigDict(frozen=True)


class NoContentResponse(_Response):
    @classmethod
    def ok_no_content(cls) -> "NoContentResponse":
        return cls()


class EmailSentResponse(_Response):
    email_id: str
    thread_uuid: str
    subject: str

    @classmethod
    def of(cls, message: Message) -> "EmailSentResponse":
        content = message.content
        return cls(
            email_id=content.id,
            thread_uuid=content.thread_uuid,
            subject=content.subject.text,
        )


class EmailDeletedResponse(_Response):
    email_id: str
    deleted_at: str
    previous_state: str

    @classmethod
    def of(cls, message: DeletedMessage) -> "EmailDeletedResponse":
        return cls(
            email_id=message.content.id,
            deleted_at=message.deleted_at.isoformat(timespec="seconds"),
            previous_state=message.previous_state.value,
        )
