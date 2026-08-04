"""
ProjetoWhatsApp

Responsável pela leitura da galeria
de mídias do WhatsApp Web.
"""

from __future__ import annotations

from services.browser_service import BrowserService
from services.logger_service import LoggerService


class GalleryService:
    """
    Serviço responsável por localizar
    todas as mídias da galeria.
    """

    def __init__(
        self,
        browser: BrowserService
    ):

        self.browser = browser

        self.log = LoggerService.app()

        self.container = None


    # ======================================================
    # Página atual
    # ======================================================

    @property
    def page(self):

        return self.browser.current_page


    # ======================================================
    # Execução principal
    # ======================================================

    def execute(self):

        self.log.info(
            "Iniciando leitura da galeria..."
        )


        self.find_gallery()


        medias = self.scan_gallery()


        self.log.success(
            f"Mídias encontradas: {len(medias)}"
        )


        return medias



    # ======================================================
    # Localizar galeria
    # ======================================================

    def find_gallery(self):

        self.log.info(
            "Procurando container da galeria..."
        )


        self.container = self.page.get_by_test_id(
            "media-gallery"
        )


        self.container.wait_for(
            timeout=15000
        )


        self.log.success(
            "Galeria encontrada pelo data-testid."
        )


        info = self.container.evaluate(
            """
            e => ({

                scrollHeight:e.scrollHeight,

                clientHeight:e.clientHeight,

                thumbs:
                e.querySelectorAll(
                    '[data-testid="image-thumb"]'
                ).length

            })
            """
        )


        self.log.info(
            f"Estado inicial galeria: {info}"
        )



    # ======================================================
    # Ler mídias
    # ======================================================

    def scan_gallery(self):


        self.log.info(
            "Capturando thumbnails..."
        )


        medias = {}


        previous_position = -1


        same_position_count = 0



        while True:


            thumbs = self.page.get_by_test_id(
                "image-thumb"
            )


            count = thumbs.count()


            self.log.info(
                f"Cards de mídia encontrados: {count}"
            )



            for index in range(count):


                try:


                    thumb = thumbs.nth(
                        index
                    )


                    key = (
                        f"media_{index}"
                    )


                    if key not in medias:


                        medias[key] = {

                            "index": index

                        }


                        self.log.debug(
                            f"Mídia adicionada: {key}"
                        )



                except Exception as error:


                    self.log.debug(
                        f"Erro capturando mídia {index}: {error}"
                    )



            # --------------------------------------------------
            # posição atual do scroll
            # --------------------------------------------------

            try:


                position = self.container.evaluate(
                    "e => e.scrollTop"
                )


                height = self.container.evaluate(
                    "e => e.scrollHeight"
                )


                client = self.container.evaluate(
                    "e => e.clientHeight"
                )



            except Exception:


                position = 0

                height = 0

                client = 0



            self.log.info(
                f"Mídias únicas: {len(medias)} "
                f"| posição {position}/{height}"
            )



            # --------------------------------------------------
            # fim da galeria
            # --------------------------------------------------

            if position == previous_position:

                same_position_count += 1


            else:

                same_position_count = 0



            if same_position_count >= 2:

                break



            if height > 0 and (
                position + client
                >=
                height - 50
            ):

                break



            previous_position = position



            # --------------------------------------------------
            # próximo carregamento
            # --------------------------------------------------

            self.container.evaluate(
                """
                e => {

                    e.scrollTop =
                    e.scrollTop + e.clientHeight;

                }
                """
            )


            self.page.wait_for_timeout(
                3000
            )



        self.log.success(
            "Fim da varredura."
        )


        result = list(
            medias.values()
        )


        self.log.success(
            f"Total retornado: {len(result)}"
        )


        if result:


            try:


                html = result[0]["locator"].evaluate(
                    """
                    e =>
                    e.outerHTML.substring(0,500)
                    """
                )


                self.log.info(
                    "Primeiro card encontrado:"
                )


                self.log.info(
                    html
                )


            except Exception:

                pass



        return result