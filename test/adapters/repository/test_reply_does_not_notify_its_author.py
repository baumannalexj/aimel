"""Replying must not notify you about your own reply.

Unread is per-recipient. The agent's poll queue and the human's inbox badge read the same rows, so a
globally-counted unread means every reply the human sends lands in the human's own unread count. The
first attempt at this fixed it by persisting the human's reply as read -- which silently broke the
agent's poll, since the agent finds waiting mail by looking for unread. Hence the count is scoped to
the recipient and the state is left alone.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from domain.message import Actor, Email
from test.fixtures.correspondence_fixtures import CorrespondenceFixtures

HUMAN = Email("alexander.baumann@aimel.com")
AGENT = Email("claude-0bd9c0c5@aimel.com")
SENT_AT = datetime(2026, 9, 7, 22, 15, tzinfo=timezone.utc)


class ReplyDoesNotNotifyItsAuthorTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = SqliteDatabaseClient(SqliteSessionFactory(Path(directory.name) / "mail.db"))
        self.addCleanup(database.close)
        self.repository = SqliteEmailRepository(database)
        self.repository.ensure_schema()

        self.opener = self.repository.add_new_thread(
            CorrespondenceFixtures.sent_email(
                sender=AGENT, recipient=HUMAN, author=Actor.AI_AGENT,
                rfc_message_id="<opener@aimel.com>", sent_at=SENT_AT,
            )
        )

    def _human_unread(self) -> int:
        return self.repository.threads_for_mailbox(HUMAN)[0].unread_count

    def _agent_waiting(self) -> list[str]:
        return [m.content.rfc_message_id for m in self.repository.list_unread(AGENT)]

    def test_the_human_replying_does_not_raise_their_own_unread_count(self) -> None:
        before = self._human_unread()

        self.repository.add_reply(
            CorrespondenceFixtures.sent_email(
                sender=HUMAN, recipient=AGENT, author=Actor.HUMAN,
                rfc_message_id="<mine@aimel.com>", sent_at=SENT_AT + timedelta(minutes=1),
            ),
            self.opener.content.id,
        )

        self.assertEqual(before, 1, "the agent's opener is genuinely unread for the human")
        self.assertEqual(
            self._human_unread(), 1, "replying notified the human about their own reply"
        )

    def test_the_agent_still_sees_the_human_reply_waiting_for_it(self) -> None:
        self.repository.add_reply(
            CorrespondenceFixtures.sent_email(
                sender=HUMAN, recipient=AGENT, author=Actor.HUMAN,
                rfc_message_id="<mine@aimel.com>", sent_at=SENT_AT + timedelta(minutes=1),
            ),
            self.opener.content.id,
        )

        self.assertIn("<mine@aimel.com>", self._agent_waiting())

    def test_a_new_email_to_the_human_still_raises_their_unread_count(self) -> None:
        self.repository.add_reply(
            CorrespondenceFixtures.sent_email(
                sender=AGENT, recipient=HUMAN, author=Actor.AI_AGENT,
                rfc_message_id="<theirs@aimel.com>", sent_at=SENT_AT + timedelta(minutes=2),
            ),
            self.opener.content.id,
        )

        self.assertEqual(self._human_unread(), 2, "real new mail must still notify")


if __name__ == "__main__":
    unittest.main()
