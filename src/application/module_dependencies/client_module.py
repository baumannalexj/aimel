from __future__ import annotations

from dataclasses import dataclass

from adapters.client.docker_compose_runtime import DockerComposeRuntime
from adapters.client.mailpit_mailbox_client import MailpitMailboxClient
from adapters.client.smtp_email_transport import SmtpEmailTransport
from common import repo_paths
from common.config import MailboxConfig, SmtpConfig
from ports.container_runtime import IContainerRuntime
from ports.email_transport import IEmailTransport
from ports.mailbox_client import IMailboxClient


@dataclass(frozen=True)
class ClientModuleConfig:
    smtp: SmtpConfig
    mailbox: MailboxConfig
    spool_port: int


class ClientModule:
    def __init__(self, config: ClientModuleConfig):
        self._transport = SmtpEmailTransport(config.smtp)
        self._mailbox = MailpitMailboxClient(config.mailbox)
        self._container_runtime = DockerComposeRuntime(repo_paths.compose_file(), config.spool_port)

    def provide_email_transport(self) -> IEmailTransport:
        return self._transport

    def provide_mailbox_client(self) -> IMailboxClient:
        return self._mailbox

    def provide_container_runtime(self) -> IContainerRuntime:
        return self._container_runtime
