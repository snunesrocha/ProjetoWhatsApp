"""
ProjetoWhatsApp

Responsável pela abertura do visualizador
e captura da mídia original (fotos e vídeos).
"""

from __future__ import annotations

from urllib.parse import urlparse
import requests

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from services.browser_service import BrowserService
from services.logger_service import LoggerService


class ViewerService:
    """
    Serviço responsável pelo visualizador de mídia.
    """

    MIN_SIZE = 50 * 1024  # 50KB

    THUMBNAIL_PATTERNS = [
        "s16", "s32", "s40", "s48", "s64", "s96", "s128",
        "dst", "thumb", "thumbnail", "preview", "tmb"
    ]

    def __init__(self, browser: BrowserService) -> None:
        self.browser = browser
        self.log = LoggerService.app()

    # ==========================================================
    # Página atual
    # ==========================================================

    @property
    def page(self):
        return self.browser.current_page

    # ==========================================================
    # Teste inicial (chamado pelo Application)
    # ==========================================================

    def test_media(
        self,
        card: object = None,
        index: int = None,
        media: dict = None
    ) -> dict | None:

        self.log.info("Testando mídia...")
        result = self.open_media(card=card, index=index, media=media)

        if result:
            self.log.success("Objeto de mídia recebido:")
            self.log.info(f"Mime : {result.get('mime')}")
            size = result.get("size", 0)
            self.log.info(f"Tamanho : {size:,} bytes")
            self.log.info(f"URL : {result.get('url')}")
            self.log.info(f"Tipo : {result.get('type')}")
        else:
            self.log.warning("Nenhuma mídia encontrada.")

        return result

    # ==========================================================
    # Abrir mídia (fluxo principal)
    # ==========================================================

    def open_media(
        self,
        card: object = None,
        index: int = None,
        media: dict = None
    ) -> dict | None:

        self.log.info("Iniciando captura da rede...")

        self.browser.network.clear()
        self.browser.network.start_capture()

        self.log.info("Abrindo mídia no visualizador...")

        try:

            # ----------------------------------------------
            # Obter card (por índice se necessário)
            # ----------------------------------------------

            if card is None and index is not None:
                card = self._get_card_by_index(index)
            elif card is None:
                card = self.get_first_media_card()
            else:
                self.log.info("Usando card específico.")

            # ----------------------------------------------
            # Rolagem até o card (usando índice)
            # ----------------------------------------------

            self._scroll_card_to_view(card, index)

            # ----------------------------------------------
            # Clique (force=True + fallback JS)
            # ----------------------------------------------

            if not self._click_card(card, index):
                raise Exception("Não foi possível clicar no card.")

            # ----------------------------------------------
            # Aguardar visualizador
            # ----------------------------------------------

            self.wait_viewer()

            # Dá tempo para as respostas de mídia
            self.page.wait_for_timeout(2000)

            # Encerra captura
            self.browser.network.stop_capture()

            # ----------------------------------------------
            # 1ª tentativa: NetworkService (blob com bytes)
            # ----------------------------------------------

            media_object = self.get_network_media()

            if media_object and self._is_media_size_valid(media_object):

                media_object = self.normalize_media(media_object)

                self.log.success(
                    "Mídia capturada via NetworkService "
                    f"({media_object.get('size', 0):,} bytes)"
                )

                return media_object

            self.log.warning(
                "NetworkService não retornou mídia válida. "
                "Usando fallback DOM..."
            )

            # ----------------------------------------------
            # 2ª tentativa: fallback via DOM do modal
            # ----------------------------------------------

            return self._capture_from_modal()

        except Exception as error:

            try:
                self.browser.network.stop_capture()
            except Exception:
                pass

            self.log.error(f"Erro ao abrir mídia: {error}")
            raise error

    # ==========================================================
    # Clique no card
    # ==========================================================

    def _click_card(
        self,
        card,
        index: int = None
    ) -> bool:

        try:

            # Tenta clique forçado (ignora overlays)
            card.click(force=True, timeout=5000)
            self.log.info("Clique forçado realizado.")
            return True

        except Exception:

            self.log.warning(
                "Clique forçado falhou. "
                "Re-buscando card por índice e tentando JavaScript..."
            )

            # Re-buscar card se índice existir
            if index is not None:

                try:

                    card = self._get_card_by_index(index)

                except Exception:

                    pass

            try:

                card.evaluate("el => el.click()")
                self.log.info("Clique via JavaScript realizado.")
                return True

            except Exception as error:

                self.log.error(f"Clique via JS também falhou: {error}")
                return False

    # ==========================================================
    # Rolagem segura (usando índice específico)
    # ==========================================================

    def _scroll_card_to_view(
        self,
        card,
        index: int = None
    ) -> None:

        try:

            card.scroll_into_view_if_needed(timeout=5000)
            self.log.success("Card rolado com sucesso.")
            return

        except Exception:

            self.log.warning(
                "scroll_into_view_if_needed falhou. "
                f"Usando rolagem manual para o índice {index}..."
            )

            try:

                # Usa o índice para rolar até o card correto
                script = f"""
                () => {{
                    const gallery = document.querySelector(
                        '[data-testid="media-gallery"]'
                    );
                    if (!gallery) return;

                    const cards = gallery.querySelectorAll(
                        '[data-testid="media-canvas"]'
                    );

                    const target = cards[{index if index is not None else 0}];

                    if (target) {{
                        target.scrollIntoView({{
                            block: "center",
                            behavior: "instant"
                        }});
                    }}
                }}
                """

                self.page.evaluate(script)
                self.page.wait_for_timeout(500)
                self.log.success("Rolagem manual executada.")

            except Exception as scroll_error:

                self.log.warning(
                    f"Falha na rolagem manual: {scroll_error}"
                )

    # ==========================================================
    # Obter card por índice
    # ==========================================================

    def _get_card_by_index(self, index: int):

        cards = self.page.get_by_test_id("media-canvas")
        count = cards.count()

        if index < 0 or index >= count:
            self.log.error(
                f"Índice {index} fora do intervalo (0-{count-1})"
            )
            raise Exception("Índice de card inválido.")

        return cards.nth(index)

    # ==========================================================
    # Aguardar visualizador
    # ==========================================================

    def wait_viewer(self):

        self.log.info("Aguardando visualizador...")

        selectors = [
            '[data-testid="media-viewer-modal"]',
            '[data-testid="media-viewer"]',
            'div[data-testid="media-viewer"]',
            'img[data-testid="media-viewer-img"]',
        ]

        for selector in selectors:

            try:

                self.page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=10000
                )

                self.log.success(
                    f"Visualizador detectado: {selector}"
                )

                return

            except PlaywrightTimeoutError:

                continue

        raise Exception("Visualizador não encontrado.")

    # ==========================================================
    # Obter mídia via NetworkService
    # ==========================================================

    def get_network_media(self) -> dict | None:
        """
        Retorna a mídia capturada pelo NetworkService.

        Nota: o NetworkService fornece `data` (bytes) mesmo quando
        a URL é um blob. Portanto, **não** filtramos por URL aqui;
        apenas garantimos que os bytes existem.
        """

        network = self.browser.network

        # API atual
        get_best = getattr(network, "get_best_media", None)
        if callable(get_best):
            self.log.info("Consultando NetworkService.get_best_media().")
            media = get_best()
            if media:
                return media

        # Compatibilidade
        get_last = getattr(network, "get_last_media", None)
        if callable(get_last):
            self.log.info("Consultando NetworkService.get_last_media().")
            media = get_last()
            if media:
                return media

        # Lista completa
        get_all = getattr(network, "get_all_media", None)
        if callable(get_all):
            all_media = get_all()
            if all_media:
                for candidate in all_media:
                    if candidate.get("data") or candidate.get("body") or candidate.get("bytes"):
                        return candidate

        return None

    # ==========================================================
    # Capturar mídia diretamente do modal (fallback)
    # ==========================================================

    def _capture_from_modal(self) -> dict | None:
        """
        Tenta extrair a URL real do elemento img/vídeo
        dentro do modal e baixar os dados.
        """

        self.log.warning("Usando fallback DOM...")
        self.log.info("Capturando URL original...")

        selectors = [
            '[data-testid="media-viewer-modal"] img',
            '[data-testid="media-viewer"] img',
            '[data-testid="media-viewer-modal"] video',
            '[data-testid="media-viewer"] video',
        ]

        selected_url = None

        for selector in selectors:

            try:

                element = self.page.locator(selector).first
                src = element.get_attribute("src", timeout=3000)

                if src and self._is_valid_media_url(src):
                    selected_url = src
                    self.log.success(f"URL capturada via {selector}")
                    break

            except Exception:

                continue

        if not selected_url:

            self.log.error(
                "Nenhuma URL de mídia válida encontrada no modal."
            )
            return None

        return self._download_from_url(selected_url)

    # ==========================================================
    # Download a partir de URL (com filtro de tamanho)
    # ==========================================================

    def _download_from_url(self, url: str) -> dict | None:

        try:

            self.log.info(f"Baixando mídia de: {url[:80]}...")

            response = requests.get(
                url,
                stream=False,
                timeout=120,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/124.0.0.0 Safari/537.36'
                    )
                }
            )

            response.raise_for_status()

            data = response.content

            # Filtro de tamanho mínimo
            if len(data) < self.MIN_SIZE:

                self.log.warning(
                    f"Mídia descartada "
                    f"({len(data):,} bytes < {self.MIN_SIZE:,} bytes)"
                )
                return None

            mime = response.headers.get('content-type', '').lower()
            media_type = self.detect_type(url)
            extension = self.detect_extension(mime, url)

            self.log.success(
                f"Mídia baixada via fallback ({len(data):,} bytes)."
            )

            return {
                "type": media_type,
                "url": url,
                "mime": mime if mime else self.detect_mime(url),
                "data": data,
                "extension": extension,
                "size": len(data),
            }

        except Exception as e:

            self.log.error(f"Falha ao baixar da URL: {e}")
            return None

    # ==========================================================
    # Verificar URL de mídia válida (para fallback DOM)
    # ==========================================================

    def _is_valid_media_url(self, url: str) -> bool:

        if not url:
            return False

        # Domínios válidos
        valid_domains = (
            "mmg.whatsapp.net",
            "cdn.whatsapp.net",
            "whatsapp.net"
        )

        if not any(domain in url for domain in valid_domains):
            return False

        # Bloquear thumbnails
        url_lower = url.lower()

        for pattern in self.THUMBNAIL_PATTERNS:

            if pattern in url_lower:
                self.log.debug(
                    f"URL rejeitada (thumbnail): {url[:100]}"
                )
                return False

        # Aceitar apenas fotos/vídeos
        allowed_extensions = (
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".mp4", ".avi", ".mov"
        )

        path = urlparse(url).path.lower()

        if not any(path.endswith(ext) for ext in allowed_extensions):
            self.log.debug(
                f"URL rejeitada (extensão não aceita): {url[:100]}"
            )
            return False

        return True

    # ==========================================================
    # Normalizar mídia (quando NetworkService fornece dados)
    # ==========================================================

    def normalize_media(self, media: dict) -> dict:

        if "data" not in media:

            if "body" in media:
                media["data"] = media["body"]

            elif "bytes" in media:
                media["data"] = media["bytes"]

        mime = (
            media.get("mime")
            or media.get("content_type")
            or ""
        ).lower()

        media["mime"] = mime

        data = media.get("data")

        if not media.get("size") and data:
            media["size"] = len(data)

        if mime.startswith("image/"):
            media["type"] = "image"

        elif mime.startswith("video/"):
            media["type"] = "video"

        else:
            media["type"] = self.detect_type(
                media.get("url", "")
            )

        media["extension"] = self.detect_extension(
            mime,
            media.get("url", "")
        )

        return media

    # ==========================================================
    # Detectar extensão
    # ==========================================================

    def detect_extension(self, mime: str, url: str) -> str:

        if "jpeg" in mime or "jpg" in mime:
            return "jpg"
        if "png" in mime:
            return "png"
        if "webp" in mime:
            return "webp"
        if "video" in mime:
            return "mp4"

        if ".jpg" in url or ".jpeg" in url:
            return "jpg"
        if ".png" in url:
            return "png"
        if ".mp4" in url:
            return "mp4"
        return "jpg"

    # ==========================================================
    # Localizar primeiro card
    # ==========================================================

    def get_first_media_card(self):

        self.log.info("Localizando primeiro card de mídia...")

        cards = self.page.get_by_test_id("media-canvas")
        count = cards.count()

        self.log.info(f"Cards encontrados: {count}")

        if count == 0:
            raise Exception(
                "Nenhum card de mídia com data-testid='media-canvas'."
            )

        return cards.first

    # ==========================================================
    # Detectar tipo
    # ==========================================================

    def detect_type(self, url: str) -> str:

        if not url:
            return "unknown"

        path = urlparse(url).path.lower()

        if ".mp4" in path:
            return "video"

        if any(ext in path for ext in (
            ".jpg", ".jpeg", ".png", ".webp", ".gif"
        )):
            return "image"

        return "unknown"

    # ==========================================================
    # Detectar MIME
    # ==========================================================

    def detect_mime(self, url: str) -> str:

        t = self.detect_type(url)

        if t == "image":
            return "image/jpeg"

        if t == "video":
            return "video/mp4"

        return ""

    # ==========================================================
    # Verificar tamanho mínimo
    # ==========================================================

    def _is_media_size_valid(self, media: dict) -> bool:

        size = media.get("size") or 0

        if not size:

            data = media.get("data")

            if data:
                size = len(data)

        return size >= self.MIN_SIZE

    # ==========================================================
    # Fechar viewer
    # ==========================================================

    def close_viewer(self):

        self.log.info("Fechando viewer...")

        try:

            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            self.log.success("Visualizador fechado.")

        except Exception as error:

            self.log.warning(f"Erro ao fechar viewer: {error}")