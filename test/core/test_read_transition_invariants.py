"""What must stay true about marking an email read, whatever the control flow becomes.

These are written to survive the rewrite in UI-11 (state transition carrying an actor). They assert
behaviour, never how it is reached, so none of them should need editing when the endpoint becomes a
PATCH with an actorId header and the repository scopes its transaction on the actor.

The bug they exist to stop from coming back: the dashboard marked a thread's newest email read on
open, including mail the human had just sent, which removed that message from the agent's unread
queue before the agent ever polled. A message sent from the app went unanswered because of it.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from domain.message import Actor, Email, MessageState
from test.fixtures.correspondence_fixtures import CorrespondenceFixtures

HUMAN = Email("alexander.baumann@aimel.com")
AGENT = Email("claude-0bd9c0c5@aimel.com")
OTHER_AGENT = Email("claude-aaaa1111@aimel.com")
SENT_AT = datetime(2026, 9, 7, 22, 15, tzinfo=timezone.utc)


class ReadTransitionInvariantsTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = SqliteDatabaseClient(SqliteSessionFactory(Path(directory.name) / "mail.db"))
        self.addCleanup(database.close)
        self.repository = SqliteEmailRepository(database)
        self.repository.ensure_schema()

        self.opener = self.repository.add_new_thread(
            self._email(AGENT, HUMAN, Actor.AI_AGENT, "<opener@aimel.com>", 0)
        )

    def _email(self, sender, recipient, author, rfc, minutes):
        return CorrespondenceFixtures.sent_email(
            sender=sender,
            recipient=recipient,
            author=author,
            rfc_message_id=rfc,
            sent_at=SENT_AT + timedelta(minutes=minutes),
        )

    def _waiting_for(self, mailbox: Email) -> set[str]:
        return {m.content.rfc_message_id for m in self.repository.list_unread(mailbox)}

    def _unread_count_for(self, mailbox: Email) -> int:
        return self.repository.threads_for_mailbox(mailbox)[0].unread_count

    def test_the_humans_reply_stays_in_the_agents_queue(self) -> None:
        """The reply is addressed to the agent, so only the agent can consume it."""
        self.repository.add_reply(
            self._email(HUMAN, AGENT, Actor.HUMAN, "<mine@aimel.com>", 1), self.opener.content.id
        )

        self.assertIn("<mine@aimel.com>", self._waiting_for(AGENT))
        self.assertNotIn("<mine@aimel.com>", self._waiting_for(HUMAN))

    def test_the_humans_reply_never_counts_toward_the_humans_own_unread(self) -> None:
        before = self._unread_count_for(HUMAN)

        self.repository.add_reply(
            self._email(HUMAN, AGENT, Actor.HUMAN, "<mine@aimel.com>", 1), self.opener.content.id
        )

        self.assertEqual(before, self._unread_count_for(HUMAN))

    def test_reading_one_email_leaves_every_other_email_in_the_thread_alone(self) -> None:
        """A transition is per email. Reading the newest must not sweep the thread."""
        second = self.repository.add_reply(
            self._email(AGENT, HUMAN, Actor.AI_AGENT, "<second@aimel.com>", 2),
            self.opener.content.id,
        )

        self.repository.mark_read(second)

        still_unread = self._waiting_for(HUMAN)
        self.assertNotIn("<second@aimel.com>", still_unread)
        self.assertIn("<opener@aimel.com>", still_unread)

    def test_mail_between_two_agents_never_enters_the_humans_queue(self) -> None:
        """Agent-to-agent traffic is visible to the human but is not theirs to consume."""
        self.repository.add_reply(
            self._email(AGENT, OTHER_AGENT, Actor.AI_AGENT, "<sidebar@aimel.com>", 3),
            self.opener.content.id,
        )

        self.assertIn("<sidebar@aimel.com>", self._waiting_for(OTHER_AGENT))
        self.assertNotIn("<sidebar@aimel.com>", self._waiting_for(HUMAN))
        self.assertEqual(self._unread_count_for(HUMAN), 1)

    def test_a_read_email_is_gone_from_the_queue_but_still_in_the_thread(self) -> None:
        """Reading moves a row between tables; it must never lose the message."""
        self.repository.mark_read(self.opener)

        self.assertEqual(self._waiting_for(HUMAN), set())
        history = self.repository.history_for_email(self.opener.content.id)
        self.assertEqual([m.content.rfc_message_id for m in history], ["<opener@aimel.com>"])
        self.assertEqual(history[0].state, MessageState.READ)


class ActorScopedTransitionTest(unittest.TestCase):
    """The hole UI-11 closes: nothing ties a read transition to the actor performing it.

    `mark_read` takes a message and moves it, full stop. No actor, so nothing stops one party
    consuming another's mail -- exactly the bug the dashboard hit by marking the human's own
    outgoing message read. The client-side `writtenByHuman()` guard is a patch over this, in the
    wrong layer: the check belongs in the transaction, scoped so a mismatched actor matches no row.

    Expected-failure on purpose. It resolves `domain.errors.NotYourEmail` at call time, so today it
    fails with AttributeError -- it cannot pass by accident. When the actor-scoped transition lands
    it passes, unittest reports an unexpected success and the suite goes red, which is the prompt to
    delete this decorator instead of leaving a stale skip behind.
    """

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = SqliteDatabaseClient(SqliteSessionFactory(Path(directory.name) / "mail.db"))
        self.addCleanup(database.close)
        self.repository = SqliteEmailRepository(database)
        self.repository.ensure_schema()

    @unittest.expectedFailure
    def test_an_actor_cannot_read_an_email_addressed_to_someone_else(self) -> None:
        from domain import errors

        addressed_to_the_agent = self.repository.add_new_thread(
            CorrespondenceFixtures.sent_email(
                sender=HUMAN,
                recipient=AGENT,
                author=Actor.HUMAN,
                rfc_message_id="<for-the-agent@aimel.com>",
                sent_at=SENT_AT,
            )
        )

        with self.assertRaises(errors.NotYourEmail):
            self.repository.mark_read(addressed_to_the_agent, actor_id=str(HUMAN))

        self.assertIn(
            "<for-the-agent@aimel.com>",
            {m.content.rfc_message_id for m in self.repository.list_unread(AGENT)},
            "the agent's mail must survive someone else trying to read it",
        )


if __name__ == "__main__":
    unittest.main()
