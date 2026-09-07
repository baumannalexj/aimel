from __future__ import annotations

from adapters.client.mailpit_mailbox_client import MailpitMailboxClient
from adapters.client.smtp_email_transport import SmtpEmailTransport
from common.config import MailboxConfig, SmtpConfig
from ports.email_transport import IEmailTransport
from ports.mailbox_client import IMailboxClient


class ClientModule:
    def __init__(self, smtp: SmtpConfig, mailbox: MailboxConfig, service_name: str):
        self._transport = SmtpEmailTransport(smtp)
        self._mailbox = MailpitMailboxClient(mailbox, service_name)

    def provide_email_transport(self) -> IEmailTransport:
        return self._transport

    def provide_mailbox_client(self) -> IMailboxClient:
        return self._mailbox
