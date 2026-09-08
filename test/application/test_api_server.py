"""HTTP-level tests for the email-lookup routes.

Real InboxService and SqliteEmailRepository on a throwaway file, only transport and mailbox
mocked -- the 404 mapping lives in the handler, not the resource, so a resource-level test would
miss a handler that forgets to catch EmailNotFound. `/api/emails/<uuid>/thread` dropped the
connection on an unknown uuid last week for exactly that reason.
"""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from adapters.resource.email_api_resource import EmailApiResource
from application.api_server import ApiServer
from common.config import NamingConfig
from common.naming import NamingPolicy
from common.thread_renderer import ThreadRenderer
from core.inbox_service import InboxService
from domain.commands import EmailSendNewThread
from domain.message import Actor, Email, EmailSubject, HtmlBody, SessionId
from test.helpers.port_mocks import PortMocks

NAMING = NamingConfig(
    service_name="aimel",
    domain="aimel.com",
    user="someone",
    human_address="{user}@{domain}",
    agent_address="claude-{session8}@{domain}",
    subject_template="{title}",
)
SESSION = SessionId("0bd9c0c5-5b21-44be-9a3b-2793b5788d05")
UNKNOWN_UUID = "00000000-0000-4000-8000-000000000000"


class EmailByUuidRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = SqliteDatabaseClient(SqliteSessionFactory(Path(directory.name) / "mail.db"))
        self.addCleanup(database.close)
        repository = SqliteEmailRepository(database)
        repository.ensure_schema()
        self.inbox = InboxService(
            repository,
            PortMocks.transport_minting_message_ids(),
            PortMocks.mailbox_holding([]),
            ThreadRenderer(),
        )
        resource = EmailApiResource(self.inbox, NamingPolicy(NAMING))

        # Bypass ApiServer.serve_forever so the test can pick an ephemeral port and shut down
        # cleanly; the handler class it builds is the thing under test either way.
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), ApiServer(resource)._handler())
        self.addCleanup(self._server.server_close)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self.addCleanup(self._server.shutdown)
        self._port = self._server.server_address[1]

        self.opener = self.inbox.send_new_thread(
            EmailSendNewThread(
                session=SESSION,
                subject=EmailSubject("the flaky auth test"),
                sender=Email("claude-0bd9c0c5@aimel.com"),
                recipient=Email("someone@aimel.com"),
                author=Actor.AI_AGENT,
                body_html=HtmlBody("<p>Reproduced it.</p>"),
                body_text="Reproduced it.",
            )
        ).content.id

    def _get(self, path: str) -> tuple[int, dict]:
        conn = http.client.HTTPConnection("127.0.0.1", self._port, timeout=5)
        self.addCleanup(conn.close)
        conn.request("GET", path)
        response = conn.getresponse()
        return response.status, json.loads(response.read())

    def test_an_unknown_uuid_returns_404_not_a_dropped_connection(self) -> None:
        status, body = self._get(f"/api/emails/{UNKNOWN_UUID}")

        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_a_known_uuid_returns_its_thread_in_the_same_shape_as_the_thread_route(self) -> None:
        status, body = self._get(f"/api/emails/{self.opener}")
        thread_status, thread_body = self._get(f"/api/emails/{self.opener}/thread")

        self.assertEqual(status, 200)
        self.assertEqual(status, thread_status)
        self.assertEqual(body, thread_body)
        self.assertEqual(body["threadUuid"], body["emails"][0]["threadUuid"])


if __name__ == "__main__":
    unittest.main()
