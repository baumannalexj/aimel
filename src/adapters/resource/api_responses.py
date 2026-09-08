"""JSON contract for the web client. camelCase, because the consumer is TypeScript."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.thread import ThreadSummary


class _Payload(BaseModel):
    model_config = ConfigDict(frozen=True)


class ThreadListItem(_Payload):
    threadUuid: str
    subject: str
    emailCount: int
    latestEmailUuid: str
    session: str
    sessionShort: str
    updatedAt: str

    @classmethod
    def of(cls, thread: ThreadSummary) -> "ThreadListItem":
        return cls(
            threadUuid=thread.thread_uuid,
            subject=thread.subject.text,
            emailCount=thread.message_count,
            latestEmailUuid=thread.latest_email_id,
            session=str(thread.session),
            sessionShort=thread.session.short,
            updatedAt=thread.updated_at.isoformat(timespec="seconds"),
        )
