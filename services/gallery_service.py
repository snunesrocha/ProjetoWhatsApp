"""
ProjetoWhatsApp

Responsável pela leitura da galeria
de mídias do WhatsApp Web.
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from services.browser_service import BrowserService
from services.logger_service import LoggerService
from constants.whatsapp_selectors import WhatsAppSelectors


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

        self.open_media_tab()

        self.find_gallery()

        medias = self.scan_gallery()

        self.log.success(
            f"Mídias encontradas: {len(medias)}"
        )

        return medias

    # ==========================================================
    # Abrir aba Mídia
    # ==========================================================

    def open_media_tab(
        self
    ):

        self.log.info(
            "Abrindo aba Mídia..."
        )

        try:

            # ------------------------------
            # Passo 1: Clicar no botão "Mídia, links e docs"
            # ------------------------------

            media_button = self.page.get_by_test_id(
                WhatsAppSelectors.MEDIA_LINKS_DOCS
            )

            # Usa force=True para ignorar possíveis overlays
            media_button.click(
                force=True,
                timeout=10000
            )

            self.page.wait_for_timeout(
                2000
            )

            # ------------------------------
            # Passo 2: Clicar na aba "Mídia"
            # ------------------------------

            gallery_tab = self.page.get_by_test_id(
                WhatsAppSelectors.GALLERY_TAB_MEDIA
            )

            # Use force=True e timeout maior
            gallery_tab.click(
                force=True,
                timeout=10000
            )

            self.page.wait_for_timeout(
                3000
            )

            self.log.success(
                "Aba Mídia aberta."
            )

        except PlaywrightTimeoutError as error:

            self.log.error(
                "Não foi possível abrir aba Mídia: "
                f"{error}"
            )

            raise

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
                    '[data-testid="media-canvas"]'
                ).length,

                children:
                e.children.length

            })
            """
        )

        self.log.info(
            f"Estado inicial galeria: {info}"
        )

        diagnostic = self.container.evaluate(
        """
        e => {

            const elements = [...e.querySelectorAll("*")];

            return {

                totalElements: elements.length,

                testids:
                    [...new Set(
                        elements
                        .map(x => x.getAttribute("data-testid"))
                        .filter(Boolean)
                    )],

                images:
                    e.querySelectorAll("img").length,

                videos:
                    e.querySelectorAll("video").length,

                classes:
                    [...new Set(
                        elements
                        .map(x => x.className)
                        .filter(x => typeof x === "string")
                    )].slice(0,20)

            }

        }
        """
        )

        self.log.info(
            f"Diagnóstico DOM galeria: {diagnostic}"
        )

        canvas_info = self.container.evaluate(
        """
        e => ({

            canvas:
                e.querySelectorAll(
                    '[data-testid="media-canvas"]'
                ).length,

            canvasImg:
                e.querySelectorAll(
                    '[data-testid="media-canvas-img"]'
                ).length,

            urlProvider:
                e.querySelectorAll(
                    '[data-testid="media-url-provider"]'
                ).length,

            firstCanvas:
                e.querySelector(
                    '[data-testid="media-canvas"]'
                )?.outerHTML.substring(0,1000)

        })
        """
        )

        self.log.info(
            f"Canvas diagnóstico: {canvas_info}"
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

            thumbs = self.container.get_by_test_id(
                "media-canvas"
            )

            count = thumbs.count()

            self.log.info(
                f"Cards de mídia encontrados na galeria: {count}"
            )

            for index in range(count):

                try:

                    thumb = thumbs.nth(
                        index
                    )

                    aria_label = thumb.get_attribute(
                        "aria-label"
                    )

                    key = f"{aria_label}|{index}"

                    if key not in medias:

                        medias[key] = {

                            "index": index,

                            "locator": thumb,

                            "label": aria_label

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

            except Exception as error:

                self.log.debug(
                    f"Erro exibindo primeiro card: {error}"
                )

        return result
    