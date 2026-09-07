from __future__ import annotations

from core.inbox_service import InboxService
from ports.email_repository import IEmailRepository
from ports.email_transport import IEmailTransport
from ports.mailbox_client import IMailboxClient


class CoreModule:
    def __init__(
        self,
        email_repository: IEmailRepository,
        email_transport: IEmailTransport,
        mailbox_client: IMailboxClient,
    ):
        self._inbox_service = InboxService(email_repository, email_transport, mailbox_client)

    def provide_inbox_service(self) -> InboxService:
        return self._inbox_service
