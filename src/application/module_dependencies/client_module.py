from __future__ import annotations

from pathlib import Path

from adapters.client.docker_compose_runtime import DockerComposeRuntime
from adapters.client.mailpit_mailbox_client import MailpitMailboxClient
from adapters.client.smtp_email_transport import SmtpEmailTransport
from common.config import MailboxConfig, SmtpConfig
from ports.container_runtime import IContainerRuntime
from ports.email_transport import IEmailTransport
from ports.mailbox_client import IMailboxClient


class ClientModule:
    def __init__(
        self,
        smtp: SmtpConfig,
        mailbox: MailboxConfig,
        service_name: str,
        compose_file: Path,
        spool_port: int,
    ):
        self._transport = SmtpEmailTransport(smtp)
        self._mailbox = MailpitMailboxClient(mailbox, service_name)
        self._container_runtime = DockerComposeRuntime(compose_file, spool_port)

    def provide_email_transport(self) -> IEmailTransport:
        return self._transport

    def provide_mailbox_client(self) -> IMailboxClient:
        return self._mailbox

    def provide_container_runtime(self) -> IContainerRuntime:
        return self._container_runtime
