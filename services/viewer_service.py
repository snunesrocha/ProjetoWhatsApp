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

    Responsabilidades:

    - localizar a primeira mídia da galeria;
    - abrir a mídia no visualizador;
    - aguardar a abertura do viewer;
    - obter a mídia capturada pelo NetworkService;
    - utilizar o método DOM apenas como fallback;
    - fechar o visualizador.
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

        result = self.open_media(
            media=media
        )

        if result:

            self.log.success(
                "Objeto de mídia recebido:"
            )

            self.log.info(
                f"Mime : {result.get('mime')}"
            )

            size = result.get("size", 0)

            self.log.info(
                f"Tamanho : {size:,} bytes"
            )

            self.log.info(
                f"URL : {result.get('url')}"
            )

            self.log.info(
                f"Tipo : {result.get('type')}"
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
            "Iniciando captura da rede..."
        )

        #
        # Limpa capturas anteriores
        #

        self.browser.network.clear()

        #
        # Inicia nova captura
        #

        self.browser.network.start_capture()

        self.log.info(
            "Abrindo mídia no visualizador..."
        )

        try:

            #
            # Localiza primeiro card
            #

            card = self.get_first_media_card()

            #
            # Garante que o card esteja visível
            #

            card.scroll_into_view_if_needed()

            self.page.wait_for_timeout(
                500
            )

            #
            # Clique
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
                    element => element.click()
                    """
                )

            #
            # Aguarda abertura do viewer
            #

            self.wait_viewer()

            #
            # Dá tempo para as respostas de mídia
            # serem processadas pelo NetworkService.
            #

            self.page.wait_for_timeout(
                2000
            )

            #
            # Encerra captura
            #

            self.browser.network.stop_capture()

            #
            # Obtém melhor mídia capturada
            #

            media = self.get_network_media()

            if media:

                #
                # Normaliza estrutura retornada
                #

                media = self.normalize_media(
                    media
                )

                self.log.success(
                    "Mídia capturada via NetworkService "
                    f"({media.get('size', 0):,} bytes)"
                )

                return media

            #
            # Fallback
            #

            self.log.warning(
                "NetworkService não capturou "
                "nenhuma mídia válida."
            )

            self.log.warning(
                "Utilizando método legado do DOM."
            )

            return self.get_original_media()

        except Exception as error:

            #
            # Garantir que a captura seja encerrada
            # mesmo em caso de erro.
            #

            try:

                self.browser.network.stop_capture()

            except Exception:

                pass

            self.log.error(
                "Erro ao abrir mídia."
            )

            raise error

    # ==========================================================
    # Obter mídia do NetworkService
    # ==========================================================

    def get_network_media(self):
        """
        Obtém a melhor mídia capturada pelo NetworkService.

        Compatibilidade:

        1. get_best_media()
        2. get_last_media()

        Isso permite que o ViewerService continue funcionando
        caso o NetworkService ainda esteja em uma versão anterior.
        """

        network = self.browser.network

        #
        # Nova API
        #

        get_best = getattr(
            network,
            "get_best_media",
            None
        )

        if callable(get_best):

            self.log.info(
                "Consultando NetworkService.get_best_media()."
            )

            media = get_best()

            if media:

                return media

        #
        # Compatibilidade com versão anterior
        #

        get_last = getattr(
            network,
            "get_last_media",
            None
        )

        if callable(get_last):

            self.log.info(
                "Consultando NetworkService.get_last_media()."
            )

            media = get_last()

            if media:

                return media

        return None

    # ==========================================================
    # Normalizar mídia
    # ==========================================================

    def normalize_media(
        self,
        media: dict
    ) -> dict:
        """
        Normaliza o objeto recebido do NetworkService.

        O DownloaderService trabalha com:

        - data
        - url
        - mime
        - size
        - type
        """

        #
        # Compatibilidade:
        #
        # versões antigas podem utilizar "body"
        # ou "bytes" em vez de "data".
        #

        if "data" not in media:

            if "body" in media:

                media["data"] = media["body"]

            elif "bytes" in media:

                media["data"] = media["bytes"]

        #
        # MIME
        #

        mime = (
            media.get("mime")
            or media.get("content_type")
            or ""
        ).lower()

        media["mime"] = mime

        #
        # Tamanho
        #

        if not media.get("size"):

            data = media.get("data")

            if data:

                media["size"] = len(data)

            else:

                media["size"] = 0

        #
        # Tipo
        #

        if mime.startswith("image/"):

            media["type"] = "image"

        elif mime.startswith("video/"):

            media["type"] = "video"

        else:

            media["type"] = self.detect_type(
                media.get("url", "")
            )

        return media

    # ==========================================================
    # Localizar primeiro card
    # ==========================================================

    def get_first_media_card(self):

        self.log.info(
            "Localizando primeiro card de mídia..."
        )

        #
        # Nova estrutura do WhatsApp Web
        #
        # A GalleryService identificou:
        #
        # data-testid="media-canvas"
        #

        cards = self.page.get_by_test_id(
            "media-canvas"
        )

        count = cards.count()

        self.log.info(
            f"Cards encontrados: {count}"
        )

        if count == 0:

            self.log.warning(
                "Nenhum media-canvas encontrado."
            )

            #
            # Diagnóstico adicional
            #

            try:

                canvas = self.page.locator(
                    '[data-testid="media-canvas"]'
                )

                canvas_count = canvas.count()

                self.log.info(
                    f"Diagnóstico media-canvas: "
                    f"{canvas_count}"
                )

            except Exception as error:

                self.log.debug(
                    f"Falha no diagnóstico: {error}"
                )

            raise Exception(
                "Nenhum card de mídia encontrado "
                "com data-testid='media-canvas'."
            )

        self.log.info(
            "Primeiro card de mídia selecionado."
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

            '[data-testid="media-viewer"]',

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
    # Captura URL original - FALLBACK
    # ==========================================================

    def get_original_media(self):

        self.log.warning(
            "Usando método legado (DOM)."
        )

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

        for index, url in enumerate(candidates):

            self.log.info(
                f"Candidata {index}: {url[:150]}"
            )

        if not candidates:

            return None

        #
        # Prioridade CDN WhatsApp
        #

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

            "type": self.detect_type(
                selected
            ),

            "url": selected,

            "mime": self.detect_mime(
                selected
            ),

            "size": 0,

            "data": None

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
        # Somente CDN WhatsApp
        #

        if "cdn.whatsapp.net" not in url:

            return False

        #
        # Rejeitar thumbnails pequenos
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
                    f"Ignorando thumbnail {size}: "
                    f"{url[:100]}"
                )

                return False

        return True

    # ==========================================================
    # Detectar tipo
    # ==========================================================

    def detect_type(
        self,
        url
    ):

        if not url:

            return "unknown"

        ext = urlparse(
            url
        ).path.lower()

        if ".mp4" in ext:

            return "video"

        if (
            ".jpg" in ext
            or ".jpeg" in ext
            or ".png" in ext
            or ".webp" in ext
        ):

            return "image"

        return "unknown"

    # ==========================================================
    # Detectar MIME
    # ==========================================================

    def detect_mime(
        self,
        url
    ):

        media_type = self.detect_type(
            url
        )

        if media_type == "image":

            return "image/jpeg"

        if media_type == "video":

            return "video/mp4"

        return ""

    # ==========================================================
    # Fechar viewer
    # ==========================================================

    def close_viewer(self):

        self.log.info(
            "Fechando viewer..."
        )

        try:

            self.page.keyboard.press(
                "Escape"
            )

            self.page.wait_for_timeout(
                500
            )

            self.log.success(
                "Visualizador fechado."
            )

        except Exception as error:

            self.log.warning(
                f"Erro ao fechar viewer: {error}"
            )
