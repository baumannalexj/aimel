from __future__ import annotations

import unittest

from adapters.repository.sql import email_sql as sql
from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from domain.message import MessageState
from test.fixtures.correspondence_fixtures import CorrespondenceFixtures
from test.helpers.port_mocks import PortMocks


class SqliteEmailRepositorySoftDeleteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database, self.transaction = PortMocks.database_client_with_transaction()
        self.repository = SqliteEmailRepository(self.database)

    def test_soft_delete_moves_the_row_inside_one_transaction_keeping_identity(self) -> None:
        message = CorrespondenceFixtures.read_message()
        self.database.query.return_value = [
            CorrespondenceFixtures.row(MessageState.DELETED)
        ]

        result = self.repository.soft_delete(message)

        # Both statements go through the transaction client, never the autocommit one.
        self.database.execute.assert_not_called()
        statements = [call.args[0] for call in self.transaction.execute.call_args_list]
        self.assertEqual(len(statements), 2)
        # Compared against the constants, so reformatting the SQL cannot break this test.
        self.assertEqual(statements[0], sql.DELETE_BY_UUID[MessageState.READ])
        self.assertEqual(statements[1], sql.INSERT_MOVED_DELETED)

        # deleted_at is absent from the insert because the schema stamps it.
        self.assertNotIn("deleted_at", statements[1])

        binds = self.transaction.execute.call_args_list[1].args[1]
        self.assertEqual(binds["uuid"], message.content.id)
        self.assertEqual(binds["previous_state"], MessageState.READ.value)
        self.assertNotIn("pk", binds)

        self.assertEqual(result.previous_state, MessageState.READ)
        self.assertEqual(result.content.id, message.content.id)


if __name__ == "__main__":
    unittest.main()
