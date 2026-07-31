"""
ProjetoWhatsApp

Responsável pela localização e abertura de uma conversa
no WhatsApp Web.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from services.browser_service import BrowserService
from services.logger_service import LoggerService
from constants.whatsapp_selectors import WhatsAppSelectors


class ConversationService:
    """
    Serviço responsável pela navegação da conversa.
    """


    def __init__(self, browser: BrowserService):

        self.browser = browser

        self.log = LoggerService.app()


    # ==========================================================
    # Page atual
    # ==========================================================

    @property
    def page(self):

        return self.browser.current_page


    # ==========================================================
    # Fluxo principal
    # ==========================================================

    def execute(self, conversation_name: str) -> None:

        self.log.info(
            f"Abrindo conversa: {conversation_name}"
        )


        self.search_conversation(
            conversation_name
        )


        self.open_conversation(
            conversation_name
        )


        self.open_info_panel()


        self.open_media_tab()


        self.log.success(
            "Conversa preparada para mídia."
        )


    # ==========================================================
    # Pesquisa conversa
    # ==========================================================

    def search_conversation(
        self,
        conversation_name: str
    ):

        self.log.info(
            "Pesquisando conversa..."
        )


        search = self.page.locator(
            WhatsAppSelectors.SEARCH_BOX
        )


        search.click()


        search.fill(
            conversation_name
        )


        self.page.wait_for_timeout(
            2000
        )


        self.log.success(
            "Pesquisa realizada."
        )


    # ==========================================================
    # Abrir conversa
    # ==========================================================

    def open_conversation(
        self,
        conversation_name: str
    ):

        self.log.info(
            "Abrindo conversa..."
        )


        try:

            item = self.page.get_by_text(
                conversation_name,
                exact=True
            ).first


            item.click()


            self.log.success(
                "Conversa aberta."
            )


        except PlaywrightTimeoutError:

            self.log.error(
                "Conversa não encontrada."
            )

            raise


    # ==========================================================
    # Abrir informações da conversa
    # ==========================================================

    def open_info_panel(self):

        self.log.info(
            "Abrindo informações da conversa..."
        )


        self.page.get_by_test_id(
            WhatsAppSelectors.CONVERSATION_INFO_HEADER
        ).click()


        self.log.success(
            "Painel de informações aberto."
        )


    # ==========================================================
    # Abrir aba mídia
    # ==========================================================

    def open_media_tab(self):

        self.log.info(
            "Abrindo aba Mídia..."
        )


        self.page.get_by_test_id(
            WhatsAppSelectors.MEDIA_LINKS_DOCS
        ).click()


        self.page.get_by_test_id(
            WhatsAppSelectors.GALLERY_TAB_MEDIA
        ).click()


        self.log.success(
            "Aba Mídia aberta."
        )