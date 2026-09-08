"""Spec'd mocks for the ports.

`create_autospec` gives the mock the port's real signature, so a typo'd method or a wrong
argument count fails the test instead of silently passing. Because every collaborator is a
constructor argument, nothing here monkeypatches anything.

Even the ones that need behaviour stay Mocks rather than hand-written fakes — a fake would lose
`assert_called_once_with` and the call log, which is usually the thing worth asserting.
"""

from __future__ import annotations

from itertools import count
from unittest.mock import Mock, create_autospec

from common.thread_renderer import ThreadRenderer
from ports.container_runtime import IContainerRuntime
from ports.database_client import IDatabaseClient
from ports.email_repository import IEmailRepository
from ports.email_transport import IEmailTransport
from ports.mailbox_client import CapturedMessage, IMailboxClient
from ports.session_repository import ISessionRepository


class PortMocks:
    @staticmethod
    def email_repository() -> Mock:
        return create_autospec(IEmailRepository, spec_set=True, instance=True)

    @staticmethod
    def session_repository() -> Mock:
        return create_autospec(ISessionRepository, spec_set=True, instance=True)

    @staticmethod
    def email_transport() -> Mock:
        return create_autospec(IEmailTransport, spec_set=True, instance=True)

    @staticmethod
    def mailbox_client() -> Mock:
        return create_autospec(IMailboxClient, spec_set=True, instance=True)

    @staticmethod
    def container_runtime() -> Mock:
        return create_autospec(IContainerRuntime, spec_set=True, instance=True)

    @staticmethod
    def thread_renderer() -> Mock:
        return create_autospec(ThreadRenderer, spec_set=True, instance=True)

    @staticmethod
    def database_client() -> Mock:
        return create_autospec(IDatabaseClient, spec_set=True, instance=True)

    @classmethod
    def database_client_with_transaction(cls) -> tuple[Mock, Mock]:
        """Returns (client, transaction_client). Statements inside a block hit the second one."""
        client = cls.database_client()
        transaction_client = cls.database_client()
        client.transaction.return_value.__enter__.return_value = transaction_client
        client.transaction.return_value.__exit__.return_value = False
        return client, transaction_client

    @classmethod
    def transport_minting_message_ids(cls) -> Mock:
        """A transport that behaves like one across calls, while still recording every call."""
        transport = cls.email_transport()
        ids = count(1)
        transport.send.side_effect = lambda *_args, **_kwargs: f"<{next(ids)}@mock.test>"
        return transport

    @classmethod
    def mailbox_holding(cls, captured: list[CapturedMessage]) -> Mock:
        mailbox = cls.mailbox_client()
        mailbox.capture.return_value = list(captured)
        mailbox.reachable.return_value = True
        return mailbox

    @classmethod
    def thread_renderer_marking_history(cls) -> Mock:
        """Renders a recognisable marker, so a test can prove history was appended."""
        renderer = cls.thread_renderer()
        renderer.render_history.side_effect = lambda messages: (
            f"<hr><details><summary>history · {len(messages)}</summary></details>"
        )
        return renderer
