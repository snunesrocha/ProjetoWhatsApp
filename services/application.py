"""
ProjetoWhatsApp

Orquestrador principal da aplicação.
"""

from __future__ import annotations


from config import Settings


from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.login_service import LoginService
from services.conversation_service import ConversationService
from services.gallery_service import GalleryService
from services.viewer_service import ViewerService
from services.logger_service import LoggerService



class Application:
    """
    Classe responsável por controlar
    o ciclo de vida da aplicação.
    """



    def __init__(
        self,
        settings: Settings
    ):


        self.settings = settings


        # Configuração dos logs
        LoggerService.configure()


        self.log = LoggerService.app()



        # Serviços

        self.database = DatabaseService()


        self.browser = BrowserService()



        self.login = LoginService(
            self.browser
        )


        self.conversation = ConversationService(
            self.browser
        )


        self.gallery = GalleryService(
            self.browser
        )


        self.viewer = ViewerService(
            self.browser
        )



    # ======================================================
    # Execução principal
    # ======================================================

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



    # ======================================================
    # Inicialização
    # ======================================================

    def initialize(
        self
    ):


        self.log.info(
            "Inicializando banco..."
        )


        self.database.initialize()



    # ======================================================
    # Fluxo principal
    # ======================================================

    def execute(
        self
    ):


        # ----------------------------------
        # Abrir navegador
        # ----------------------------------

        self.browser.start()



        self.browser.open_whatsapp()



        # ----------------------------------
        # Login
        # ----------------------------------

        self.login.execute()



        # ----------------------------------
        # Abrir conversa
        # ----------------------------------

        self.conversation.execute(

            self.settings.CONVERSATION_NAME

        )



        # ----------------------------------
        # Ler galeria
        # ----------------------------------

        medias = self.gallery.execute()



        self.log.success(
            f"{len(medias)} mídias encontradas."
        )



        # ----------------------------------
        # TESTE VIEWER
        # abre somente a primeira foto
        # ----------------------------------

        if medias:


            self.log.info(
                "Testando primeira mídia..."
            )


            self.viewer.test_media(
                medias[0]
            )


        else:


            self.log.warning(
                "Nenhuma mídia encontrada."
            )



    # ======================================================
    # Finalização normal
    # ======================================================

    def finish(
        self
    ):


        self.log.success(
            "Processamento finalizado."
        )



    # ======================================================
    # Encerramento
    # ======================================================

    def shutdown(
        self
    ):


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