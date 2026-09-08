"""Real SQLite, no mocks — proves the inbox scoping SQL, not just that it was called.

A mocked database can only prove the right bind values were passed; it cannot prove the
query actually excludes the rows it should. This exercises `threads_for_mailbox` against
real rows so the (a)-vs-(b) choice — a thread stays in the mailbox once addressed to it,
even after later replies move on to other agents — is actually verified.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from domain.commands import SentEmail
from domain.message import Actor, Email, EmailSubject, HtmlBody, SessionId

SESSION = SessionId("0bd9c0c5-5b21-44be-9a3b-2793b5788d05")
HUMAN = Email("alexander.baumann@aimel.com")
AGENT_ONE = Email("claude-0bd9c0c5@aimel.com")
AGENT_TWO = Email("claude-1234abcd@aimel.com")
START = datetime(2026, 9, 7, 22, 0, tzinfo=timezone.utc)


class ThreadsForMailboxTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        factory = SqliteSessionFactory(Path(self._directory.name) / "mail.db")
        self.database = SqliteDatabaseClient(factory)
        self.addCleanup(self.database.close)
        self.repository = SqliteEmailRepository(self.database)
        self.repository.ensure_schema()

    def _sent(self, subject: str, sender: Email, recipient: Email, offset: int) -> SentEmail:
        return SentEmail(
            session=SESSION,
            subject=EmailSubject(subject),
            sender=sender,
            recipient=recipient,
            author=Actor.AI_AGENT,
            rfc_message_id=f"<{subject}-{offset}@aimel.com>",
            in_reply_to="",
            references=(),
            body_html=HtmlBody(f"<p>{subject}</p>"),
            body_text=subject,
            sent_at=START + timedelta(minutes=offset),
        )

    def test_a_thread_addressed_to_the_human_stays_even_after_agents_take_it_over(self) -> None:
        opener = self.repository.add_new_thread(self._sent("status check", AGENT_ONE, HUMAN, 0))
        # The human opened it, an agent replied to the human, then two agents kept talking —
        # the latest email is agent-to-agent, but the human was addressed once.
        self.repository.add_reply(
            self._sent("status check", AGENT_ONE, AGENT_TWO, 1), opener.content.id
        )

        mailbox = self.repository.threads_for_mailbox(HUMAN)

        self.assertEqual([t.subject.text for t in mailbox], ["status check"])
        self.assertEqual(mailbox[0].message_count, 2)

    def test_a_purely_agent_to_agent_thread_never_shows_up_in_the_human_inbox(self) -> None:
        self.repository.add_new_thread(self._sent("build failed", AGENT_ONE, AGENT_TWO, 0))

        mailbox = self.repository.threads_for_mailbox(HUMAN)

        self.assertEqual(mailbox, [])
        # Sanity check: the thread is real, just not addressed to the human.
        self.assertEqual(len(self.repository.all_threads()), 1)


if __name__ == "__main__":
    unittest.main()
