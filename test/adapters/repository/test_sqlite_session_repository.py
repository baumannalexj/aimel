from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from adapters.database.sqlite_database_client import SqliteDatabaseClient, SqliteSessionFactory
from adapters.repository.sql import session_sql as sql
from adapters.repository.sqlite_session_repository import SqliteSessionRepository
from domain.message import SessionId
from test.helpers.port_mocks import PortMocks

SESSION_ID = SessionId("0bd9c0c5-5b21-44be-9a3b-2793b5788d05")


class SqliteSessionRepositoryStatementTest(unittest.TestCase):
    """Which statement runs and what it binds — checked against mocks, not a real database."""

    def setUp(self) -> None:
        self.database = PortMocks.database_client()
        self.repository = SqliteSessionRepository(self.database)

    def test_ensure_schema_creates_the_table(self) -> None:
        self.repository.ensure_schema()

        self.database.execute.assert_called_once_with(sql.CREATE_TABLE)

    def test_register_upserts_then_reloads_by_session_id(self) -> None:
        self.database.query.return_value = [
            {
                "uuid": "11111111-2222-4333-8444-555555555555",
                "session_id": str(SESSION_ID),
                "created_at": "2026-09-07T22:16:00Z",
                "last_seen_at": "2026-09-07T22:16:00Z",
                "email_count": 1,
            }
        ]

        result = self.repository.register(SESSION_ID)

        self.database.execute.assert_called_once_with(sql.REGISTER, {"session_id": str(SESSION_ID)})
        self.database.query.assert_called_once_with(
            sql.SELECT_BY_SESSION_ID, {"session_id": str(SESSION_ID)}
        )
        self.assertEqual(result.session_id, SESSION_ID)
        self.assertEqual(result.email_count, 1)

    def test_find_returns_none_when_the_session_is_unknown(self) -> None:
        self.database.query.return_value = []

        self.assertIsNone(self.repository.find(SESSION_ID))


class SqliteSessionRepositoryUpsertTest(unittest.TestCase):
    """Real SQLite, so the schema defaults and the ON CONFLICT clause actually run."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)

        factory = SqliteSessionFactory(Path(self._directory.name) / "sessions.db")
        self.database = SqliteDatabaseClient(factory)
        self.addCleanup(self.database.close)
        self.repository = SqliteSessionRepository(self.database)
        self.repository.ensure_schema()

    def test_registering_the_same_session_three_times_leaves_exactly_one_row(self) -> None:
        for _ in range(3):
            self.repository.register(SESSION_ID)

        rows = self.database.query("SELECT * FROM sessions")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["session_id"], str(SESSION_ID))
        self.assertEqual(rows[0]["email_count"], 3)

    def test_registering_twice_advances_last_seen_at_without_touching_created_at(self) -> None:
        first = self.repository.register(SESSION_ID)
        second = self.repository.register(SESSION_ID)

        self.assertEqual(first.created_at, second.created_at)
        self.assertGreaterEqual(second.last_seen_at, first.last_seen_at)

    def test_schema_defaults_populate_uuid_and_created_at_without_the_caller_supplying_them(
        self,
    ) -> None:
        registered = self.repository.register(SESSION_ID)

        self.assertTrue(registered.id)
        self.assertIsNotNone(registered.created_at)
        self.assertIsNotNone(registered.last_seen_at)

    def test_two_different_sessions_get_two_rows(self) -> None:
        other = SessionId("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")

        self.repository.register(SESSION_ID)
        self.repository.register(other)

        self.assertEqual(len(self.repository.list_all()), 2)
        self.assertIsNotNone(self.repository.find(SESSION_ID))
        self.assertIsNotNone(self.repository.find(other))


if __name__ == "__main__":
    unittest.main()
