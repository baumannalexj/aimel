"""Spec'd mocks for the ports.

`create_autospec` gives the mock the port's real signature, so a typo'd method or a wrong
argument count fails the test instead of silently passing. Because every collaborator is a
constructor argument, nothing here monkeypatches anything.
"""

from __future__ import annotations

from unittest.mock import create_autospec

from common.thread_renderer import ThreadRenderer
from ports.database_client import IDatabaseClient
from ports.email_repository import IEmailRepository
from ports.email_transport import IEmailTransport
from ports.mailbox_client import IMailboxClient


class PortMocks:
    @staticmethod
    def email_repository():
        return create_autospec(IEmailRepository, spec_set=True, instance=True)

    @staticmethod
    def email_transport():
        return create_autospec(IEmailTransport, spec_set=True, instance=True)

    @staticmethod
    def mailbox_client():
        return create_autospec(IMailboxClient, spec_set=True, instance=True)

    @staticmethod
    def thread_renderer():
        return create_autospec(ThreadRenderer, spec_set=True, instance=True)

    @staticmethod
    def database_client():
        return create_autospec(IDatabaseClient, spec_set=True, instance=True)

    @classmethod
    def database_client_with_transaction(cls):
        """Returns (client, transaction_client). Statements inside a block hit the second one."""
        client = cls.database_client()
        transaction_client = cls.database_client()
        client.transaction.return_value.__enter__.return_value = transaction_client
        client.transaction.return_value.__exit__.return_value = False
        return client, transaction_client
