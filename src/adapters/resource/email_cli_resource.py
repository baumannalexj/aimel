from __future__ import annotations

from adapters.resource.requests import (
    DrainRequest,
    ListRequest,
    MessageRequest,
    PollRequest,
    SendRequest,
    SessionRequest,
    ThreadRequest,
)
from common.naming import NamingPolicy
from core.inbox_service import InboxService
from domain.message import (
    Author,
    DeletedMessage,
    Email,
    Message,
    ReadMessage,
    UnreadMessage,
)
from domain.outgoing import Draft
from domain.thread import ThreadSummary


class EmailCliResource:
    """Upstream adapter. Receives typed requests and builds the domain models core needs."""

    def __init__(self, inbox_service: InboxService, naming_policy: NamingPolicy):
        self._inbox = inbox_service
        self._naming = naming_policy

    def send(self, request: SendRequest) -> UnreadMessage:
        thread = self._inbox.resolve_thread(request.session, request.thread)
        history = self._inbox.history(request.session, thread)
        if history:
            # The subject is the thread's context, set once when it opens.
            subject = history[0].content.subject
        elif request.title:
            subject = self._naming.subject_for(request.session, thread, request.title)
        else:
            raise ValueError(f"thread '{thread}' is new — pass --title to open it")

        human = self._naming.human_address(request.session)
        agent = self._naming.agent_address(request.session)
        from_human = request.author is Author.HUMAN
        return self._inbox.send_email(
            Draft(
                session=request.session,
                thread=thread,
                subject=subject,
                sender=human if from_human else agent,
                recipient=agent if from_human else human,
                author=request.author,
                body_html=request.html,
                body_text=request.text,
                include_history=request.include_history,
            )
        )

    def poll(self, request: PollRequest) -> list[UnreadMessage]:
        mailbox = self.mailbox_for(request)
        if request.thread is None:
            return self._inbox.poll(mailbox, limit=request.limit)
        thread = self._inbox.resolve_thread(request.session, request.thread)
        return self._inbox.poll_thread(mailbox, thread, limit=request.limit)

    def read(self, request: MessageRequest) -> ReadMessage:
        return self._inbox.read(request.message_id)

    def delete(self, request: MessageRequest) -> DeletedMessage:
        return self._inbox.delete(request.message_id)

    def history(self, request: ThreadRequest) -> list[Message]:
        thread = self._inbox.resolve_thread(request.session, request.thread)
        return self._inbox.history(request.session, thread)

    def threads(self, request: SessionRequest) -> list[ThreadSummary]:
        return self._inbox.threads(request.session)

    def deleted(self, request: ListRequest) -> list[Message]:
        return self._inbox.deleted(limit=request.limit)

    def drain(self, request: DrainRequest) -> list[UnreadMessage]:
        return self._inbox.drain(purge=request.purge, limit=request.limit)

    def mailbox_for(self, request: PollRequest) -> Email:
        if request.mailbox_owner is Author.HUMAN:
            return self._naming.human_address(request.session)
        return self._naming.agent_address(request.session)
