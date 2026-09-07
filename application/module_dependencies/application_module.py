from __future__ import annotations

from application.module_dependencies.client_module import ClientModule
from application.module_dependencies.core_module import CoreModule
from application.module_dependencies.database_module import DatabaseModule
from application.module_dependencies.repository_module import RepositoryModule
from common.config import AppConfig
from core.inbox_service import InboxService


class ApplicationModule:
    """Composition root. Every singleton is built here, in dependency order."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.database_module = DatabaseModule(config.database)
        self.repository_module = RepositoryModule(
            self.database_module.provide_database_client()
        )
        self.client_module = ClientModule(
            config.smtp, config.mailbox, config.naming.service_name
        )
        self.core_module = CoreModule(
            self.repository_module.provide_email_repository(),
            self.client_module.provide_email_transport(),
            self.client_module.provide_mailbox_client(),
        )

    def provide_inbox_service(self) -> InboxService:
        return self.core_module.provide_inbox_service()

    def close(self) -> None:
        self.database_module.close()
