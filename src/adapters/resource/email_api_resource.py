"""JSON resource for the web client. Maps domain models to the wire contract, nothing else."""

from __future__ import annotations

from adapters.resource.api_responses import ThreadListItem
from core.inbox_service import InboxService


class EmailApiResource:
    def __init__(self, inbox_service: InboxService):
        self._inbox = inbox_service

    def threads(self) -> list[ThreadListItem]:
        """Every session's threads — one inbox spanning agents."""
        return [ThreadListItem.of(thread) for thread in self._inbox.all_threads()]
