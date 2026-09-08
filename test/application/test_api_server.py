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
from adapters.resource.session_directory_resource import SessionDirectoryApiResource
from adapters.resource.skill_resource import SkillResource
from common.skill_catalog import SkillCatalog
from application.api_server import ApiServer
from common.config import NamingConfig
from common.naming import NamingPolicy
from common.session_directory import SessionDirectory
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
        sessions = SessionDirectoryApiResource(SessionDirectory(Path(directory.name) / "no-such-dir"))

        self.skill_directory = Path(directory.name) / "skill"
        self.skill_directory.mkdir()
        # Named SKILL.md with frontmatter, exactly like the real one. A fixture called aimel.md
        # with no frontmatter is what let the name and summary both ship wrong.
        (self.skill_directory / "SKILL.md").write_text(
            "---\nname: aimel\ndescription: How an agent talks to a human by email.\n---\n\n"
            "# aimel\n\nBody text.\n",
            encoding="utf-8",
        )
        skills = SkillResource(SkillCatalog(self.skill_directory))

        # Bypass ApiServer.serve_forever so the test can pick an ephemeral port and shut down
        # cleanly; the handler class it builds is the thing under test either way.
        self._server = ThreadingHTTPServer(
            ("127.0.0.1", 0), ApiServer(resource, sessions, skills)._handler()
        )
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
        status, _, body = self._get_text(path)
        return status, json.loads(body)

    def _get_json(self, path: str) -> tuple[int, dict]:
        return self._get(path)

    def _get_text(self, path: str) -> tuple[int, str, str]:
        conn = http.client.HTTPConnection("127.0.0.1", self._port, timeout=5)
        self.addCleanup(conn.close)
        conn.request("GET", path)
        response = conn.getresponse()
        return (
            response.status,
            response.getheader("Content-Type") or "",
            response.read().decode("utf-8"),
        )

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

    def test_the_skills_listing_says_what_each_skill_is_and_where_to_get_it(self) -> None:
        status, body = self._get_json("/api/skills")
        self.assertEqual(status, 200)
        self.assertEqual(len(body), 1)
        listed = body[0]
        self.assertEqual(listed["name"], "aimel")
        self.assertEqual(listed["summary"], "How an agent talks to a human by email.")
        self.assertEqual(listed["markdownPath"], "/api/skills/aimel")
        self.assertGreater(listed["byteCount"], 0)
    def test_a_skill_is_served_as_markdown_not_wrapped_in_json(self) -> None:
        status, content_type, body = self._get_text("/api/skills/aimel")
        self.assertEqual(status, 200)
        self.assertIn("text/markdown", content_type)
        self.assertTrue(body.startswith("---"))
        self.assertIn("# aimel", body)
    def test_an_unknown_skill_is_a_404(self) -> None:
        status, body = self._get_json("/api/skills/nope")
        self.assertEqual(status, 404)
        self.assertIn("nope", body["error"])
    def test_a_path_that_is_not_a_skill_name_does_not_reach_the_catalog(self) -> None:
        """The name pattern is the guard: no traversal, no absolute paths."""
        for path in ("/api/skills/../secrets", "/api/skills/a/b", "/api/skills/"):
            with self.subTest(path=path):
                status, _ = self._get_json(path)
                self.assertEqual(status, 404)
    def test_an_edited_skill_is_served_without_restarting(self) -> None:
        (self.skill_directory / "SKILL.md").write_text(
            "---\nname: aimel\ndescription: d\n---\n\nRewritten.\n", encoding="utf-8"
        )
        _, _, body = self._get_text("/api/skills/aimel")
        self.assertIn("Rewritten.", body)


if __name__ == "__main__":
    unittest.main()
