"""
ProjetoWhatsApp

Responsável pela abertura do visualizador
e preparação da captura da mídia original.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from services.browser_service import BrowserService
from services.logger_service import LoggerService


class ViewerService:
    """
    Serviço responsável pelo visualizador de mídia.
    """


    def __init__(
        self,
        browser: BrowserService
    ):

        self.browser = browser

        self.log = LoggerService.app()


    # ==========================================================
    # Página atual
    # ==========================================================

    @property
    def page(self):

        return self.browser.current_page


    # ==========================================================
    # Teste inicial
    # ==========================================================

    def test_media(
        self,
        media=None
    ):

        self.log.info(
            "Testando primeira mídia..."
        )

        self.open_media(
            media
        )

        url = self.get_original_media()

        if url:

            self.log.success(
                f"Mídia encontrada: {url[:80]}"
            )

        else:

            self.log.warning(
                "URL original não encontrada."
            )


    # ==========================================================
    # Abrir mídia
    # ==========================================================

    def open_media(
        self,
        media=None
    ):

        self.log.info(
            "Abrindo mídia no visualizador..."
        )


        try:

            card = self.get_first_media_card()


            card.scroll_into_view_if_needed()


            self.page.wait_for_timeout(
                1000
            )


            #
            # Primeiro tenta clique normal
            #

            try:

                self.log.info(
                    "Tentando clique normal..."
                )


                card.click(
                    timeout=3000
                )


            except Exception:


                self.log.warning(
                    "Clique normal bloqueado. "
                    "Executando clique JavaScript..."
                )


                card.evaluate(
                    """
                    element => {
                        element.click();
                    }
                    """
                )


            self.page.wait_for_timeout(
                3000
            )


            self.wait_viewer()


            self.log.success(
                "Mídia aberta no visualizador."
            )


        except Exception as error:


            self.log.error(
                "Não foi possível abrir mídia."
            )

            raise error



    # ==========================================================
    # Localizar primeiro card
    # ==========================================================

    def get_first_media_card(self):


        self.log.info(
            "Localizando primeiro card de mídia..."
        )


        cards = self.page.get_by_test_id(
            "image-thumb"
        )


        count = cards.count()


        self.log.info(
            f"Cards encontrados: {count}"
        )


        if count == 0:

            raise Exception(
                "Nenhum card de mídia encontrado."
            )


        card = cards.first


        self.log.info(
            "Primeiro card selecionado."
        )


        return card



    # ==========================================================
    # Aguarda viewer
    # ==========================================================

    def wait_viewer(self):


        self.log.info(
            "Aguardando visualizador..."
        )


        selectors = [

            '[data-testid="media-viewer-modal"]',

            '[role="dialog"]',

            '[data-animate-modal-popup="true"]',

            'img[src*="whatsapp"]'

        ]


        for selector in selectors:


            try:


                self.page.wait_for_selector(

                    selector,

                    state="visible",

                    timeout=3000

                )


                self.log.success(

                    f"Visualizador detectado: {selector}"

                )


                return



            except PlaywrightTimeoutError:


                continue



        raise Exception(
            "Visualizador não abriu."
        )



    # ==========================================================
    # Captura URL original
    # ==========================================================

    def get_original_media(self):


        self.log.info(
            "Capturando URL original..."
        )


        images = self.page.locator(
            "img"
        )


        total = images.count()


        self.log.info(
            f"Imagens encontradas no viewer: {total}"
        )


        for index in range(total):


            img = images.nth(index)


            try:


                src = img.get_attribute(
                    "src"
                )


                if src and "whatsapp" in src:


                    self.log.success(
                        "URL encontrada."
                    )


                    return src



            except:


                continue



        return None



    # ==========================================================
    # Fechar visualizador
    # ==========================================================

    def close_viewer(self):


        self.log.info(
            "Fechando visualizador..."
        )


        self.page.keyboard.press(
            "Escape"
        )


        self.page.wait_for_timeout(
            1000
        )


        self.log.success(
            "Visualizador fechado."
        )