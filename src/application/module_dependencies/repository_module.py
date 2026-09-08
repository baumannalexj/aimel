from __future__ import annotations

from adapters.repository.sqlite_email_repository import SqliteEmailRepository
from ports.database_client import IDatabaseClient
from ports.email_repository import IEmailRepository


class RepositoryModule:
    """Takes the database client port, not the module, so it cannot reach the driver."""

    def __init__(self, database_client: IDatabaseClient):
        self._email_repository = SqliteEmailRepository(database_client)
        self._email_repository.ensure_schema()

    def provide_email_repository(self) -> IEmailRepository:
        return self._email_repository
