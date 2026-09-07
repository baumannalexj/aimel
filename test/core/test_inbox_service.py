from __future__ import annotations

import unittest

from core.inbox_service import InboxService
from test.fixtures.correspondence_fixtures import CorrespondenceFixtures
from test.helpers.port_mocks import PortMocks


class InboxServiceReadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = PortMocks.email_repository()
        self.transport = PortMocks.email_transport()
        self.mailbox = PortMocks.mailbox_client()
        self.renderer = PortMocks.thread_renderer()
        self.service = InboxService(
            self.repository, self.transport, self.mailbox, self.renderer
        )

    def test_read_delegates_the_state_change_and_returns_the_persisted_shape(self) -> None:
        unread = CorrespondenceFixtures.unread_message()
        persisted = CorrespondenceFixtures.read_message()
        self.repository.find.return_value = unread
        self.repository.mark_read.return_value = persisted

        result = self.service.read(unread.content.id)

        self.repository.find.assert_called_once_with(unread.content.id)
        self.repository.mark_read.assert_called_once_with(unread)
        self.assertIs(result, persisted)
        # Reading must not put anything on the wire.
        self.transport.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
