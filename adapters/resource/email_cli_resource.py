from __future__ import annotations

from dataclasses import dataclass

from common.config import NamingConfig
from common import naming as naming_helpers
from common.session import resolve as resolve_session
from core.inbox_service import InboxService
from domain.message import (
    Author,
    DeletedMessage,
    Message,
    ReadMessage,
    ThreadSlug,
    UnreadMessage,
)
from domain.outgoing import Draft
from domain.thread import Thread


@dataclass(frozen=True)
class SendRequest:
    session: str
    thread: str
    title: str
    html: str
    text: str
    as_human: bool
    include_history: bool


@dataclass(frozen=True)
class PollRequest:
    session: str
    thread: str
    as_human: bool
    limit: int


@dataclass(frozen=True)
class ThreadRequest:
    session: str
    thread: str


@dataclass(frozen=True)
class MessageRequest:
    message_id: str


class EmailCliResource:
    """Upstream adapter. Marshals argv into request objects, then builds domain models."""

    def __init__(self, inbox_service: InboxService, naming: NamingConfig):
        self._inbox = inbox_service
        self._naming = naming

    def send(self, request: SendRequest) -> UnreadMessage:
        session = resolve_session(request.session)
        if request.thread:
            thread = ThreadSlug(request.thread)
        elif request.title:
            thread = ThreadSlug.from_title(request.title)
        else:
            raise ValueError("pass --thread or --title so the correspondence has a thread")

        history = self._inbox.history(session, thread)
        if history:
            subject = history[0].content.subject
        elif request.title:
            subject = naming_helpers.subject_for(self._naming, session, thread, request.title)
        else:
            raise ValueError(f"thread '{thread}' is new — pass --title to open it")

        human = naming_helpers.human_address(self._naming, session)
        agent = naming_helpers.agent_address(self._naming, session)
        author = Author.HUMAN if request.as_human else Author.AGENT
        draft = Draft(
            session=session,
            thread=thread,
            subject=subject,
            sender=human if request.as_human else agent,
            recipient=agent if request.as_human else human,
            author=author,
            body_html=request.html,
            body_text=request.text,
            include_history=request.include_history,
        )
        return self._inbox.send(draft)

    def poll(self, request: PollRequest) -> list[UnreadMessage]:
        session = resolve_session(request.session)
        mailbox = (
            naming_helpers.human_address(self._naming, session)
            if request.as_human
            else naming_helpers.agent_address(self._naming, session)
        )
        thread = ThreadSlug(request.thread) if request.thread else None
        return self._inbox.poll(mailbox, thread=thread, limit=request.limit)

    def read(self, request: MessageRequest) -> ReadMessage:
        return self._inbox.read(request.message_id)

    def delete(self, request: MessageRequest) -> DeletedMessage:
        return self._inbox.delete(request.message_id)

    def history(self, request: ThreadRequest) -> list[Message]:
        session = resolve_session(request.session)
        return self._inbox.history(session, ThreadSlug(request.thread))

    def threads(self, session_value: str) -> list[Thread]:
        return self._inbox.threads(resolve_session(session_value))

    def deleted(self, limit: int = 50) -> list[Message]:
        return self._inbox.deleted(limit=limit)

    def drain(self, purge: bool, limit: int = 200) -> list[UnreadMessage]:
        return self._inbox.drain(purge=purge, limit=limit)

    def mailbox_for(self, session_value: str, as_human: bool) -> str:
        session = resolve_session(session_value)
        resolver = (
            naming_helpers.human_address if as_human else naming_helpers.agent_address
        )
        return str(resolver(self._naming, session))
