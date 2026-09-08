"""JSON resource for the web client. Maps domain models to the wire contract, nothing else."""

from __future__ import annotations

from adapters.resource.api_responses import EmailItem, ReplyAccepted, ThreadDetail, ThreadListItem
from adapters.resource.requests import ReplyRequest
from common.naming import NamingPolicy
from domain.commands import IncludeHistory
from domain.errors import EmailNotFound
from domain.message import Actor, SessionId
from core.inbox_service import InboxService


class EmailApiResource:
    def __init__(self, inbox_service: InboxService, naming_policy: NamingPolicy):
        self._inbox = inbox_service
        self._naming = naming_policy

    def threads(self) -> list[ThreadListItem]:
        """Every session's threads — one inbox spanning agents."""
        return [ThreadListItem.of(thread) for thread in self._inbox.all_threads()]

    def thread(self, email_uuid: str) -> ThreadDetail | None:
        """The whole thread containing that email, newest first."""
        messages = self._inbox.history(email_uuid)
        return ThreadDetail.of(messages) if messages else None

    def mark_read(self, email_uuid: str) -> EmailItem:
        """Moves the email to read and reports its new state. Raises ValueError if it does
        not exist, or if it is deleted — the caller maps those to the right status code."""
        return EmailItem.of(self._inbox.read(email_uuid))

    def reply(self, email_uuid: str, markup: str) -> ReplyAccepted:
        """Answers on the thread, addressed from the answered email's session."""
        history = self._inbox.history(email_uuid)
        if not history:
            raise EmailNotFound(email_uuid)
        session = history[0].content.session
        request = ReplyRequest(
            session=str(session),
            email_id=email_uuid,
            html=markup,
            actor=Actor.HUMAN,
            include_history=IncludeHistory.ALL,
        )
        sent = self._inbox.reply(
            request.to_domain(
                SessionId(str(session)),
                self._naming.human_address(session),
                self._naming.agent_address(session),
            )
        )
        return ReplyAccepted.of(sent)
