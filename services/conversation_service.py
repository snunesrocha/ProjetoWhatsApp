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


    def __init__(
        self,
        browser: BrowserService
    ):

        self.browser = browser

        self.log = LoggerService.app()



    # ==========================================================
    # Página atual do navegador
    # ==========================================================

    @property
    def page(self):

        page = self.browser.current_page


        if page is None:

            raise RuntimeError(
                "Página do WhatsApp não inicializada."
            )


        return page



    # ==========================================================
    # Fluxo principal
    # ==========================================================

    def execute(
        self,
        conversation_name: str
    ) -> None:


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




        self.log.success(
            "Conversa preparada para mídia."
        )



    # ==========================================================
    # Pesquisar conversa
    # ==========================================================

    def search_conversation(
        self,
        conversation_name: str
    ):


        self.log.info(
            "Pesquisando conversa..."
        )


        search_box = self.page.locator(
            WhatsAppSelectors.SEARCH_BOX
        )


        search_box.wait_for(
            state="visible",
            timeout=10000
        )


        search_box.click()


        search_box.fill(
            conversation_name
        )


        self.page.wait_for_timeout(
            2000
        )


        self.log.success(
            "Pesquisa realizada."
        )



    # ==========================================================
    # Abrir conversa encontrada
    # ==========================================================

    def open_conversation(
        self,
        conversation_name: str
    ):


        self.log.info(
            "Abrindo conversa..."
        )


        try:


            # seletor mais específico
            # evita clicar em textos internos
            conversation = self.page.locator(
                f"span[title='{conversation_name}']"
            ).first



            conversation.wait_for(
                state="visible",
                timeout=10000
            )


            conversation.click()



            self.page.wait_for_timeout(
                2000
            )


            self.log.success(
                "Conversa aberta."
            )



        except PlaywrightTimeoutError:


            self.log.error(
                f"Conversa não encontrada: {conversation_name}"
            )


            raise



    # ==========================================================
    # Abrir painel de informações
    # ==========================================================

    def open_info_panel(
        self
    ):


        self.log.info(
            "Abrindo informações da conversa..."
        )



        try:


            info_header = self.page.get_by_test_id(
                WhatsAppSelectors.CONVERSATION_INFO_HEADER
            )


            info_header.wait_for(
                state="visible",
                timeout=10000
            )


            info_header.click()



            self.page.wait_for_timeout(
                2000
            )


            self.log.success(
                "Painel de informações aberto."
            )



        except PlaywrightTimeoutError:


            self.log.error(
                "Painel de informações não encontrado."
            )


            raise



    # # ==========================================================
    # # Abrir aba Mídia
    # # ==========================================================

    # def open_media_tab(
    #     self
    # ):


    #     self.log.info(
    #         "Abrindo aba Mídia..."
    #     )



    #     try:


    #         media_button = self.page.get_by_test_id(
    #             WhatsAppSelectors.MEDIA_LINKS_DOCS
    #         )


    #         media_button.wait_for(
    #             state="visible",
    #             timeout=10000
    #         )


    #         media_button.click()



    #         self.page.wait_for_timeout(
    #             2000
    #         )



    #         gallery_tab = self.page.get_by_test_id(
    #             WhatsAppSelectors.GALLERY_TAB_MEDIA
    #         )


    #         gallery_tab.wait_for(
    #             state="visible",
    #             timeout=10000
    #         )


    #         gallery_tab.click()



    #         self.page.wait_for_timeout(
    #             3000
    #         )



    #         self.log.success(
    #             "Aba Mídia aberta."
    #         )



    #     except PlaywrightTimeoutError:


    #         self.log.error(
    #             "Não foi possível abrir aba Mídia."
    #         )


    #         raise