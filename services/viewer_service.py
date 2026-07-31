"""
ProjetoWhatsApp

Responsável pela abertura do visualizador
e captura da mídia original.
"""

from __future__ import annotations

import base64

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from services.browser_service import BrowserService
from services.logger_service import LoggerService



class ViewerService:


    def __init__(
        self,
        browser: BrowserService
    ):

        self.browser = browser

        self.log = LoggerService.app()



    @property
    def page(self):

        return self.browser.current_page



    # ======================================================
    # Teste mídia
    # ======================================================

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


        result = self.extract_media()



        if result:


            self.log.success(
                "Objeto de mídia recebido:"
            )


            self.log.info(
                f"Tipo: {result['type']}"
            )


            self.log.info(
                f"Tamanho bytes: {len(result['data'])}"
            )


        else:


            self.log.warning(
                "Não foi possível extrair mídia."
            )



        return result





    # ======================================================
    # Abrir visualizador
    # ======================================================

    def open_media(
        self,
        media=None
    ):


        self.log.info(
            "Abrindo mídia no visualizador..."
        )


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



        self.page.wait_for_timeout(
            3000
        )



        self.wait_viewer()



        self.log.success(
            "Mídia aberta no visualizador."
        )





    # ======================================================
    # Primeiro card
    # ======================================================

    def get_first_media_card(self):


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



        return cards.first





    # ======================================================
    # Aguarda viewer
    # ======================================================

    def wait_viewer(self):


        selectors = [

            '[data-testid="media-viewer-modal"]',

            '[role="dialog"]'

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
            "Viewer não encontrado."
        )





    # ======================================================
    # Extrair mídia completa
    # ======================================================

    def extract_media(self):


        self.log.info(
            "Capturando blob da mídia..."
        )



        blob_url = self.get_blob_url()



        if not blob_url:


            self.log.error(
                "Blob não encontrado."
            )

            return None




        self.log.info(
            f"Blob encontrado: {blob_url}"
        )



        data = self.download_blob(
            blob_url
        )



        if not data:


            return None




        return {


            "type": "image",

            "extension": "jpg",

            "data": data

        }





    # ======================================================
    # Localiza blob
    # ======================================================

    def get_blob_url(self):


        images = self.page.locator(
            "img"
        )


        total = images.count()



        for i in range(total):


            src = images.nth(i).get_attribute(
                "src"
            )



            if src and src.startswith("blob:"):


                return src



        return None





    # ======================================================
    # Converte blob para bytes
    # ======================================================

    def download_blob(
        self,
        blob_url
    ):


        script = """

        async (url)=>{

            const response = await fetch(url);

            const blob = await response.blob();

            const buffer = await blob.arrayBuffer();

            let binary = '';

            const bytes = new Uint8Array(buffer);


            for(let i=0;i<bytes.length;i++){

                binary += String.fromCharCode(bytes[i]);

            }


            return btoa(binary);

        }

        """



        try:


            result = self.page.evaluate(

                script,

                blob_url

            )



            return base64.b64decode(
                result
            )



        except Exception as error:


            self.log.error(
                f"Erro ao converter blob: {error}"
            )


            return None





    def close_viewer(self):


        self.page.keyboard.press(
            "Escape"
        )