from __future__ import annotations

from adapters.resource.requests import (
    DeleteRequest,
    DrainRequest,
    EmailIdRequest,
    ListRequest,
    PollRequest,
    ReplyRequest,
    SendNewThreadRequest,
    SessionScopedRequest,
)
from common.naming import NamingPolicy
from common.session import SessionDetector
from core.inbox_service import InboxService
from domain.message import (
    Actor,
    DeletedMessage,
    Email,
    Message,
    ReadMessage,
    SessionId,
    UnreadMessage,
)
from domain.thread import ThreadSummary


class EmailCliResource:
    """Upstream adapter. Validated requests in, domain commands out."""

    def __init__(
        self,
        inbox_service: InboxService,
        naming_policy: NamingPolicy,
        session_detector: SessionDetector,
    ):
        self._inbox = inbox_service
        self._naming = naming_policy
        self._sessions = session_detector

    def send_new_thread(self, request: SendNewThreadRequest) -> UnreadMessage:
        session = self._sessions.resolve(request.session)
        sender, recipient = self._pair(session, request.actor is Actor.HUMAN)
        subject = self._naming.subject_for(session, request.title)
        return self._inbox.send_new_thread(
            request.to_domain(session, sender, recipient, subject)
        )

    def reply(self, request: ReplyRequest) -> UnreadMessage:
        session = self._sessions.resolve(request.session)
        sender, recipient = self._pair(session, request.actor is Actor.HUMAN)
        return self._inbox.reply(request.to_domain(session, sender, recipient))

    def delete(self, request: DeleteRequest) -> DeletedMessage:
        return self._inbox.delete(request.to_domain())

    def read(self, request: EmailIdRequest) -> ReadMessage:
        return self._inbox.read(request.email_id)

    def history(self, request: EmailIdRequest) -> list[Message]:
        return self._inbox.history(request.email_id)

    def poll(self, request: PollRequest) -> list[UnreadMessage]:
        return self._inbox.poll(self.mailbox_for(request), limit=request.limit)

    def threads(self, request: SessionScopedRequest) -> list[ThreadSummary]:
        return self._inbox.threads(self._sessions.resolve(request.session))

    def deleted(self, request: ListRequest) -> list[Message]:
        return self._inbox.deleted(limit=request.limit)

    def drain(self, request: DrainRequest) -> list[UnreadMessage]:
        return self._inbox.drain(purge=request.purge, limit=request.limit)

    def mailbox_for(self, request: PollRequest) -> Email:
        session = self._sessions.resolve(request.session)
        if request.mailbox_owner is Actor.HUMAN:
            return self._naming.human_address(session)
        return self._naming.agent_address(session)

    def _pair(self, session: SessionId, as_human: bool) -> tuple[Email, Email]:
        human = self._naming.human_address(session)
        agent = self._naming.agent_address(session)
        return (human, agent) if as_human else (agent, human)
