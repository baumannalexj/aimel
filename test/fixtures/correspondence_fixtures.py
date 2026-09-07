"""Builders for domain objects and database rows used across tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.message import (
    Author,
    Correspondence,
    Email,
    MessageState,
    ReadMessage,
    SessionId,
    ThreadSlug,
    UnreadMessage,
)

SESSION = "0bd9c0c5-5b21-44be-9a3b-2793b5788d05"
UUID = "11111111-2222-4333-8444-555555555555"
SENT_AT = datetime(2026, 9, 7, 22, 15, tzinfo=timezone.utc)
CREATED_AT = datetime(2026, 9, 7, 22, 16, tzinfo=timezone.utc)
READ_AT = datetime(2026, 9, 7, 22, 30, tzinfo=timezone.utc)
DELETED_AT = datetime(2026, 9, 7, 22, 45, tzinfo=timezone.utc)


class CorrespondenceFixtures:
    @staticmethod
    def content(**overrides: Any) -> Correspondence:
        defaults: dict[str, Any] = {
            "id": UUID,
            "created_at": CREATED_AT,
            "session": SessionId(SESSION),
            "thread": ThreadSlug("building-claude-email-service"),
            "subject": "0bd9c0c5: building claude email service",
            "sender": Email("claude-0bd9c0c5@aimel.com"),
            "recipient": Email("someone@aimel.com"),
            "author": Author.AGENT,
            "rfc_message_id": "<abc@aimel.com>",
            "in_reply_to": "",
            "references": (),
            "body_html": "<p>body</p>",
            "body_text": "body",
            "sent_at": SENT_AT,
        }
        return Correspondence(**(defaults | overrides))

    @classmethod
    def unread_message(cls, **overrides: Any) -> UnreadMessage:
        return UnreadMessage(content=cls.content(**overrides))

    @classmethod
    def read_message(cls, **overrides: Any) -> ReadMessage:
        return ReadMessage(content=cls.content(**overrides), read_at=READ_AT)

    @classmethod
    def row(cls, state: MessageState, **overrides: Any) -> dict[str, Any]:
        content = cls.content()
        row: dict[str, Any] = {
            "pk": 1,
            "uuid": content.id,
            "created_at": "2026-09-07T22:16:00Z",
            "session": str(content.session),
            "thread": str(content.thread),
            "subject": content.subject,
            "sender": content.sender.address,
            "recipient": content.recipient.address,
            "author": content.author.value,
            "rfc_message_id": content.rfc_message_id,
            "in_reply_to": "",
            "refs": "",
            "body_html": content.body_html,
            "body_text": content.body_text,
            "sent_at": "2026-09-07T22:15:00Z",
        }
        if state is MessageState.READ:
            row["read_at"] = "2026-09-07T22:30:00Z"
        if state is MessageState.DELETED:
            row["previous_state"] = MessageState.READ.value
            row["deleted_at"] = "2026-09-07T22:45:00Z"
        return row | overrides
