"""DatabaseStats reports what someone would actually want to know about the mail store's size."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from common.database_stats import (
    ContentSizeReport,
    DatabaseFileSizes,
    DatabaseStats,
    ReclaimableSpace,
    TableRowCounts,
)
from domain.commands import SentEmail
from domain.message import Actor, Email, EmailSubject, HtmlBody, SessionId
from test.helpers.port_mocks import PortMocks

SESSION = SessionId("0bd9c0c5-5b21-44be-9a3b-2793b5788d05")


def _sent(body_html: str, body_text: str, rfc: str) -> SentEmail:
    return SentEmail(
        session=SESSION,
        subject=EmailSubject("size check"),
        sender=Email("claude-0bd9c0c5@aimel.com"),
        recipient=Email("someone@aimel.com"),
        author=Actor.AI_AGENT,
        rfc_message_id=rfc,
        in_reply_to="",
        references=(),
        body_html=HtmlBody(body_html),
        body_text=body_text,
        sent_at=datetime(2026, 9, 7, 22, 15, tzinfo=timezone.utc),
    )


class DatabaseStatsComputedFieldsTest(unittest.TestCase):
    """The derived properties, without touching a database at all."""

    def test_file_sizes_total_sums_the_database_and_both_sidecars(self) -> None:
        sizes = DatabaseFileSizes(database_bytes=100, wal_bytes=250, shm_bytes=10)
        self.assertEqual(sizes.total_bytes, 360)

    def test_row_counts_total_sums_every_state(self) -> None:
        counts = TableRowCounts(unread=2, read=3, deleted=1)
        self.assertEqual(counts.total, 6)

    def test_overhead_is_the_database_file_minus_its_content(self) -> None:
        content = ContentSizeReport(content_bytes=44_000, database_bytes=136_000)
        self.assertEqual(content.overhead_bytes, 92_000)

    def test_reclaimable_bytes_is_freelist_pages_times_page_size(self) -> None:
        reclaimable = ReclaimableSpace(freelist_pages=12, page_size=4096)
        self.assertEqual(reclaimable.reclaimable_bytes, 49_152)


class DatabaseStatsFileSizesFromDiskTest(unittest.TestCase):
    """Filesystem facts, isolated from SQL so WAL checkpoint timing can't flake the assertion."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.database_path = Path(self._directory.name) / "mail.db"

        self.database = PortMocks.database_client()
        self.database.identifier.side_effect = lambda name: f'"{name}"'
        self.database.query.return_value = [
            {"count": 0, "bytes": 0, "freelist_count": 0, "page_size": 4096}
        ]
        self.stats = DatabaseStats(self.database, self.database_path)

    def test_a_database_with_no_sidecars_yet_reports_zero_for_both(self) -> None:
        self.database_path.write_bytes(b"x" * 136_000)

        report = self.stats.collect()

        self.assertEqual(report.file_sizes.database_bytes, 136_000)
        self.assertEqual(report.file_sizes.wal_bytes, 0)
        self.assertEqual(report.file_sizes.shm_bytes, 0)
        self.assertEqual(report.file_sizes.total_bytes, 136_000)

    def test_a_wal_file_larger_than_the_database_is_still_counted_in_full(self) -> None:
        self.database_path.write_bytes(b"x" * 1_000)
        self.database_path.with_name("mail.db-wal").write_bytes(b"y" * 5_000)

        report = self.stats.collect()

        self.assertEqual(report.file_sizes.database_bytes, 1_000)
        self.assertEqual(report.file_sizes.wal_bytes, 5_000)
        self.assertEqual(report.file_sizes.total_bytes, 6_000)


class DatabaseStatsAgainstARealDatabaseTest(unittest.TestCase):
    """Real SQLite file under /tmp, real repository, so the maths runs against real rows."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.database_path = Path(self._directory.name) / "mail.db"

        factory = SqliteSessionFactory(self.database_path)
        self.database = SqliteDatabaseClient(factory)
        self.addCleanup(self.database.close)
        self.repository = SqliteEmailRepository(self.database)
        self.repository.ensure_schema()

        self.stats = DatabaseStats(self.database, self.database_path)

    def test_row_counts_match_where_each_message_was_left(self) -> None:
        unread = self.repository.add_new_thread(_sent("<p>one</p>", "one", "<1@aimel.com>"))
        self.repository.add_new_thread(_sent("<p>two</p>", "two", "<2@aimel.com>"))
        self.repository.mark_read(unread)

        report = self.stats.collect()

        self.assertEqual(report.row_counts, TableRowCounts(unread=1, read=1, deleted=0))

    def test_content_bytes_matches_the_body_html_and_body_text_actually_inserted(self) -> None:
        self.repository.add_new_thread(_sent("<p>hello</p>", "hello", "<3@aimel.com>"))
        self.repository.add_new_thread(_sent("<p>world!</p>", "world!", "<4@aimel.com>"))

        report = self.stats.collect()

        expected = len("<p>hello</p>") + len("hello") + len("<p>world!</p>") + len("world!")
        self.assertEqual(report.content.content_bytes, expected)
        self.assertEqual(report.content.database_bytes, self.database_path.stat().st_size)
        self.assertEqual(
            report.content.overhead_bytes, report.content.database_bytes - expected
        )

    def test_content_bytes_counts_utf8_bytes_and_not_characters(self) -> None:
        html, text = "<p>café — \U0001f9c0</p>", "café — \U0001f9c0"
        self.repository.add_new_thread(_sent(html, text, "<5@aimel.com>"))

        report = self.stats.collect()

        expected = len(html.encode("utf-8")) + len(text.encode("utf-8"))
        self.assertEqual(report.content.content_bytes, expected)
        self.assertGreater(expected, len(html) + len(text))

    def test_reclaimable_space_is_read_from_the_live_pragmas(self) -> None:
        report = self.stats.collect()

        self.assertGreater(report.reclaimable.page_size, 0)
        self.assertGreaterEqual(report.reclaimable.freelist_pages, 0)


if __name__ == "__main__":
    unittest.main()
