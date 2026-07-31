"""
ProjetoWhatsApp

Orquestrador principal da aplicação.
"""

from __future__ import annotations

from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.login_service import LoginService
from services.conversation_service import ConversationService
from services.logger_service import LoggerService


class Application:


    def __init__(self, settings):

        self.settings = settings

        LoggerService.configure()

        self.log = LoggerService.app()

        self._create_services()


    def _create_services(self):

        self.database = DatabaseService()

        self.browser = BrowserService()

        self.login = LoginService(
            self.browser
        )

        self.conversation = ConversationService(
            self.browser
        )


    def run(self) -> None:

        self.log.info(
            "Inicializando aplicação..."
        )

        try:

            self.initialize()

            self.execute()

            self.finish()


        except KeyboardInterrupt:

            self.log.warning(
                "Execução interrompida pelo usuário."
            )


        except Exception:

            LoggerService.error().exception(
                "Erro inesperado durante a execução."
            )


        finally:

            self.shutdown()


    def initialize(self):

        self.log.info(
            "Inicializando banco..."
        )

        self.database.initialize()


    def execute(self):

        self.browser.start()

        self.browser.open_whatsapp()

        self.login.execute()

        self.conversation.execute(
            self.settings.CONVERSATION_NAME
        )


    def finish(self):

        self.log.success(
            "Processamento finalizado."
        )


    def shutdown(self):

        try:
            self.database.disconnect()

        except Exception:
            pass


        try:
            self.browser.stop()

        except Exception:
            pass


        self.log.info(
            "Aplicação encerrada."
        )