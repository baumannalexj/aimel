"""End to end through the real stack, with only the outside world mocked.

Real repository on a throwaway SQLite file, real InboxService, real resource, real naming. The
transport and the spool are Mocks so nothing touches SMTP — and being Mocks rather than fakes, the
test can also assert they were called.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from adapters.resource.email_cli_resource import EmailCliResource
from adapters.resource.requests import (
    DeleteRequest,
    EmailIdRequest,
    PollRequest,
    ReplyRequest,
    SendNewThreadRequest,
    SessionScopedRequest,
)
from common.config import NamingConfig
from common.naming import NamingPolicy
from common.thread_renderer import ThreadRenderer
from core.inbox_service import InboxService
from domain.message import Actor, MessageState
from test.helpers.port_mocks import PortMocks

SESSION = UUID("0bd9c0c5-5b21-44be-9a3b-2793b5788d05")
EXPECTED = json.loads((Path(__file__).parent.parent / "fixtures" / "correspondence_flow.json").read_text())

NAMING = NamingConfig(
    service_name="aimel",
    domain="aimel.com",
    user="someone",
    human_address="{user}@{domain}",
    agent_address="claude-{session8}@{domain}",
    subject_template="{title}",
)


class CorrespondenceFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)

        factory = SqliteSessionFactory(Path(self._directory.name) / "mail.db")
        self.database = SqliteDatabaseClient(factory)
        self.addCleanup(self.database.close)
        self.repository = SqliteEmailRepository(self.database)
        self.repository.ensure_schema()

        self.transport = PortMocks.transport_minting_message_ids()
        self.mailbox = PortMocks.mailbox_holding([])
        self.inbox = InboxService(
            self.repository, self.transport, self.mailbox, ThreadRenderer()
        )
        self.resource = EmailCliResource(self.inbox, NamingPolicy(NAMING))

    # --- helpers ---

    def _send(self, title: str, html: str) -> str:
        request = SendNewThreadRequest(
            session=SESSION, title=title, html=html, actor=Actor.AI_AGENT
        )
        return self.resource.send_new_thread(request).content.id

    def _reply(self, email_id: str, html: str, actor: Actor) -> str:
        request = ReplyRequest(session=SESSION, email_id=email_id, html=html, actor=actor)
        return self.resource.reply(request).content.id

    # --- the flow ---

    def test_send_then_reply_both_ways_then_read_the_thread_back(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)
        self._reply(opener, "<p>Fixed and green.</p>", Actor.AI_AGENT)

        history = self.resource.history(EmailIdRequest(email_id=UUID(opener)))

        self.assertEqual(len(history), EXPECTED["thread"]["email_count"])
        self.assertEqual(
            [
                {
                    "author": message.content.author.value,
                    "state": message.state.value,
                    "preview": message.content.preview,
                }
                for message in history
            ],
            EXPECTED["emails_newest_first"],
        )
        # One thread, so every email shares its uuid.
        self.assertEqual({message.content.thread_uuid for message in history}, {history[0].content.thread_uuid})

    def test_every_email_went_through_the_transport_with_a_growing_chain(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)
        self._reply(opener, "<p>Fixed and green.</p>", Actor.AI_AGENT)

        self.assertEqual(self.transport.send.call_count, EXPECTED["wire"]["sent_count"])
        envelopes = [call.args[0] for call in self.transport.send.call_args_list]

        self.assertEqual(len({envelope.subject.text for envelope in envelopes}), 1)
        self.assertEqual(envelopes[0].in_reply_to, "")
        self.assertEqual(
            [len(envelope.references) for envelope in envelopes],
            EXPECTED["wire"]["reference_counts"],
        )

    def test_reading_and_deleting_move_rows_without_losing_the_thread(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)
        third = self._reply(opener, "<p>Fixed and green.</p>", Actor.AI_AGENT)

        self.resource.read(EmailIdRequest(email_id=UUID(opener)))
        self.resource.delete(DeleteRequest(email_id=UUID(third)))

        expected = EXPECTED["after_read_and_delete"]
        self.assertEqual(len(self.repository.list_by_state(MessageState.UNREAD)), expected["unread"])
        self.assertEqual(len(self.repository.list_by_state(MessageState.READ)), expected["read"])
        self.assertEqual(
            len(self.repository.list_by_state(MessageState.DELETED)), expected["deleted"]
        )
        history = self.resource.history(EmailIdRequest(email_id=UUID(opener)))
        self.assertEqual(len(history), expected["history_still_shows"])

    def test_polling_shows_what_is_addressed_to_the_agent(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)

        waiting = self.resource.poll(
            PollRequest(session=SESSION, mailbox_owner=Actor.AI_AGENT, limit=50)
        )

        self.assertEqual([message.content.preview for message in waiting], ["ship it behind a flag"])

    def test_threads_reports_one_row_for_the_thread(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)

        threads = self.resource.threads(SessionScopedRequest(session=SESSION))

        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].subject.text, EXPECTED["thread"]["subject"])
        self.assertEqual(threads[0].message_count, 2)

    def test_unread_count_tracks_reads_within_the_thread(self) -> None:
        opener = self._send("the flaky auth test", "<p>Reproduced it.</p>")
        self._reply(opener, "<p>ship it behind a flag</p>", Actor.HUMAN)

        before = self.resource.threads(SessionScopedRequest(session=SESSION))
        self.assertEqual(before[0].unread_count, 2)

        self.resource.read(EmailIdRequest(email_id=UUID(opener)))

        after = self.resource.threads(SessionScopedRequest(session=SESSION))
        self.assertEqual(after[0].unread_count, 1)
        self.assertEqual(after[0].message_count, 2)


if __name__ == "__main__":
    unittest.main()
