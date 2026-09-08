"""JSON resource for the web client. Maps domain models to the wire contract, nothing else."""

from __future__ import annotations

from adapters.resource.api_responses import ThreadDetail, ThreadListItem
from core.inbox_service import InboxService


class EmailApiResource:
    def __init__(self, inbox_service: InboxService):
        self._inbox = inbox_service

    def threads(self) -> list[ThreadListItem]:
        """Every session's threads — one inbox spanning agents."""
        return [ThreadListItem.of(thread) for thread in self._inbox.all_threads()]

    def thread(self, email_uuid: str) -> ThreadDetail | None:
        """The whole thread containing that email, newest first."""
        messages = self._inbox.history(email_uuid)
        return ThreadDetail.of(messages) if messages else None
