from __future__ import annotations

from adapters.resource.email_cli_resource import EmailCliResource
from application.cli_request_marshaller import CliRequestMarshaller
from application.module_dependencies.client_module import ClientModule
from application.module_dependencies.common_module import CommonModule
from application.module_dependencies.core_module import CoreModule
from application.module_dependencies.database_module import DatabaseModule
from application.module_dependencies.repository_module import RepositoryModule
from common.config import AppConfig
from common.session_color import SessionColorPalette
from core.inbox_service import InboxService


class ApplicationModule:
    """Composition root. Every singleton is built here, in dependency order."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.common_module = CommonModule(config.naming)
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
            self.common_module.provide_thread_renderer(),
        )
        self._email_cli_resource = EmailCliResource(
            self.core_module.provide_inbox_service(),
            self.common_module.provide_naming_policy(),
            self.common_module.provide_session_detector(),
        )
        self._cli_request_marshaller = CliRequestMarshaller()

    def provide_cli_request_marshaller(self) -> CliRequestMarshaller:
        return self._cli_request_marshaller

    def provide_inbox_service(self) -> InboxService:
        return self.core_module.provide_inbox_service()

    def provide_email_cli_resource(self) -> EmailCliResource:
        return self._email_cli_resource

    def provide_session_colors(self) -> SessionColorPalette:
        return self.common_module.provide_session_colors()

    def close(self) -> None:
        self.database_module.close()
