"""
ProjetoWhatsApp

Orquestrador principal da aplicação.
"""

from __future__ import annotations
from services.logger_service import LoggerService
from services.database_service import DatabaseService
from services.browser_service import BrowserService
from services.login_service import LoginService
from services.conversation_service import ConversationService

class Application:

    def _create_services(self):

        self.database = DatabaseService()

        self.browser = BrowserService()

        self.login = LoginService(self.browser)

    def __init__(self):

        LoggerService.configure()

        self.log = LoggerService.app()

        self._create_services()


    def run(self) -> None:
        """
        Fluxo principal da aplicação.
        """

        self.log.info("Inicializando aplicação...")

        try:

            #
            # Etapa 1
            #
            self.initialize()

            #
            # Etapa 2
            #
            self.execute()

            #
            # Etapa 3
            #
            self.finish()

        except KeyboardInterrupt:

            self.log.warning("Execução interrompida pelo usuário.")

        except Exception:

            LoggerService.error().exception(
                "Erro inesperado durante a execução."
            )

        finally:

            self.shutdown()

    def initialize(self):

        self.log.info("Inicializando aplicação...")

        self.database.initialize()
        
    def execute(self):

        self.browser.start()

        self.browser.open_whatsapp()

        self.login.execute()

        self.conversation.execute()

    def finish(self) -> None:
        """
        Executado quando o processamento termina com sucesso.
        """

        self.log.success("Processamento finalizado.")

    def shutdown(self):

        self.database.disconnect()

        self.browser.stop()

        self.log.info("Aplicação encerrada.")
