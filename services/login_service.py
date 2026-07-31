"""
ProjetoWhatsApp

Responsável pelo gerenciamento da autenticação no WhatsApp Web.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError

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

    # ---------------------------------------------------------
    # Property
    # ---------------------------------------------------------

    @property
    def page(self):
        """
        Sempre retorna a página atual do BrowserService.
        Nunca mantém uma referência antiga.
        """

        return self.browser.current_page

    # ---------------------------------------------------------
    # Sessão autenticada?
    # ---------------------------------------------------------

    def is_logged(self) -> bool:

        self.log.debug(
            "Verificando se existe sessão autenticada..."
        )

        try:

            self.page.wait_for_selector(

                WhatsAppSelectors.SEARCH_BOX,

                timeout=3000

            )

            return True

        except TimeoutError:

            return False

    # ---------------------------------------------------------
    # Aguarda login
    # ---------------------------------------------------------

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

            timeout=0

        )

        self.log.success(
            "Login realizado."
        )

    # ---------------------------------------------------------
    # Aguarda Home
    # ---------------------------------------------------------

    def wait_home(self) -> None:

        self.log.info(
            "Aguardando carregamento do WhatsApp..."
        )

        self.page.wait_for_selector(

            WhatsAppSelectors.SEARCH_BOX,

            timeout=0

        )

        self.log.success(
            "WhatsApp pronto."
        )

    # ---------------------------------------------------------
    # Fluxo completo
    # ---------------------------------------------------------

    def execute(self) -> None:

        self.wait_login()

        self.wait_home()