"""
ProjetoWhatsApp

Responsável pela abertura do visualizador
e captura da mídia original.
"""

from __future__ import annotations

from urllib.parse import urlparse

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


        result = self.open_media()


        if result:


            self.log.success(
                "Objeto de mídia recebido:"
            )


            self.log.info(
                f"Tipo: {result['type']}"
            )


            self.log.info(
                f"URL: {result['url']}"
            )


        else:


            self.log.warning(
                "Nenhuma mídia encontrada."
            )



        return result



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
                    element => element.click()
                    """
                )



            self.wait_viewer()


            self.log.success(
                "Mídia aberta no visualizador."
            )


            return self.get_original_media()



        except Exception as error:


            self.log.error(
                "Erro ao abrir mídia."
            )


            raise error




    # ==========================================================
    # Localizar card
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
                "Nenhum card encontrado."
            )



        self.log.info(
            "Primeiro card selecionado."
        )


        return cards.first




    # ==========================================================
    # Esperar viewer
    # ==========================================================

    def wait_viewer(self):


        self.log.info(
            "Aguardando visualizador..."
        )



        selectors = [

            '[data-testid="media-viewer-modal"]',

            '[role="dialog"]',

            'img[src*="media.whatsapp"]',

            'img[src*="cdn.whatsapp"]'

        ]



        for selector in selectors:


            try:


                self.page.wait_for_selector(

                    selector,

                    state="visible",

                    timeout=5000

                )


                self.log.success(

                    f"Visualizador detectado: {selector}"

                )


                return



            except PlaywrightTimeoutError:


                continue



        raise Exception(
            "Visualizador não encontrado."
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



        candidates = []



        for index in range(total):


            try:


                src = images.nth(index).get_attribute(
                    "src"
                )



                if not src:
                    continue



                self.log.info(
                    f"URL {index}: {src[:120]}"
                )



                if self.is_valid_candidate(src):


                    candidates.append(src)



            except Exception:


                continue



        self.log.info(
            f"Candidatas válidas: {len(candidates)}"
        )



        for index,url in enumerate(candidates):


            self.log.info(
                f"Candidata {index}: {url[:150]}"
            )



        if not candidates:


            return None



        # Prioridade CDN WhatsApp

        selected = None


        for url in candidates:


            if "cdn.whatsapp.net" in url:


                selected = url

                break



        if not selected:


            selected = candidates[0]



        self.log.success(
            "Mídia original selecionada."
        )



        return {


            "type": self.detect_type(selected),

            "url": selected

        }




    # ==========================================================
    # Filtro de URL
    # ==========================================================

    def is_valid_candidate(
        self,
        url: str
    ):


        invalid = [

            "blob:",

            "emoji",

            "static.whatsapp",

            "web.whatsapp.com",

            "profile",

            "avatar",

            "data:image"

        ]


        for item in invalid:


            if item in url:


                self.log.info(
                    f"Ignorando thumbnail: {url[:100]}"
                )


                return False



        #
        # somente CDN WhatsApp
        #

        if "cdn.whatsapp.net" not in url:


            return False



        #
        # rejeitar thumbnails pequenos
        #

        thumbnail_sizes = [

            "s16",

            "s32",

            "s40",

            "s48",

            "s64",

            "s96",

            "s128"

        ]



        for size in thumbnail_sizes:


            if f"dst-jpg_{size}" in url:


                self.log.info(
                    f"Ignorando thumbnail {size}: {url[:100]}"
                )


                return False



        #
        # aceitar s9, s10, etc
        # normalmente são imagens grandes
        #

        return True



    # ==========================================================
    # Detectar tipo
    # ==========================================================

    def detect_type(
        self,
        url
    ):


        ext = urlparse(url).path.lower()



        if ".mp4" in ext:


            return "video"



        if ".jpg" in ext or ".jpeg" in ext or ".png" in ext:


            return "image"



        return "unknown"




    # ==========================================================
    # Fechar viewer
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