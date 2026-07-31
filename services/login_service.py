"""
ProjetoWhatsApp

Responsável pelo gerenciamento da autenticação no WhatsApp Web.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.whatsapp_selectors import WhatsAppSelectors
from services.browser_service import BrowserService
from services.logger_service import LoggerService


class LoginService:
    """
    Serviço responsável pela autenticação.
    """


    def __init__(self, browser: BrowserService):

        self.browser = browser

        self.log = LoggerService.app()


    @property
    def page(self):

        return self.browser.current_page


    def is_logged(self) -> bool:

        self.log.debug(
            "Verificando se existe sessão autenticada..."
        )


        if not self.page:

            self.log.error(
                "Página do navegador não inicializada."
            )

            return False


        try:

            self.page.wait_for_selector(

                WhatsAppSelectors.SEARCH_BOX,

                timeout=3000

            )

            return True


        except PlaywrightTimeoutError:

            return False



    def wait_login(self) -> None:


        if self.is_logged():

            self.log.success(
                "Sessão autenticada."
            )

            return



        self.log.warning(
            "Login necessário."
        )


        self.log.info(
            "Aguardando leitura do QR Code..."
        )


        self.page.wait_for_selector(

            WhatsAppSelectors.SEARCH_BOX,

            timeout=120000

        )


        self.log.success(
            "Login realizado."
        )



    def wait_home(self) -> None:


        self.log.info(
            "Aguardando carregamento do WhatsApp..."
        )


        self.page.wait_for_selector(

            WhatsAppSelectors.SEARCH_BOX,

            timeout=30000

        )


        self.log.success(
            "WhatsApp pronto."
        )



    def execute(self) -> None:


        self.wait_login()

        self.wait_home()