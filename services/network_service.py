"""
ProjetoWhatsApp

Serviço responsável por interceptar as respostas HTTP
do WhatsApp Web.

Responsabilidade:

- observar respostas da rede;
- identificar imagens e vídeos;
- ignorar thumbnails;
- aceitar URLs blob: quando o MIME for imagem/vídeo;
- armazenar o conteúdo binário em "data";
- fornecer a melhor mídia capturada ao ViewerService.

Não realiza download em arquivo.

O DownloaderService é responsável por persistir
a mídia posteriormente.
"""

from __future__ import annotations

from threading import Lock

from playwright.sync_api import Response

from services.logger_service import LoggerService


class NetworkService:
    """
    Captura respostas HTTP contendo imagens ou vídeos.
    """

    # ==========================================================
    # Configurações
    # ==========================================================

    DEBUG_ALL_RESPONSES = True

    MIN_MEDIA_SIZE = 15_000

    THUMBNAIL_MARKERS = (
        "dst-jpg_s16",
        "dst-jpg_s32",
        "dst-jpg_s40",
        "dst-jpg_s48",
        "dst-jpg_s64",
        "dst-jpg_s96",
        "dst-jpg_s128",
    )

    INVALID_URL_MARKERS = (
        "data:image",
        "static.whatsapp",
        "web.whatsapp.com",
        "emoji",
        "profile",
        "avatar",
    )

    MEDIA_DOMAINS = (
        "cdn.whatsapp.net",
        "mmg.whatsapp.net",
        "media.",
        "lookaside",
    )

    # ==========================================================
    # Inicialização
    # ==========================================================

    def __init__(self):

        self.log = LoggerService.app()

        self.log.info(
            f"NetworkService carregado de: {__file__}"
        )

        self._capturing = False

        self._responses = []

        self._lock = Lock()

        self._registered = False

    # ==========================================================
    # Registro
    # ==========================================================

    def register(self, page):
        """
        Registra o callback de respostas do Playwright.

        Deve ser executado apenas uma vez.
        """

        if self._registered:

            self.log.debug(
                "NetworkService já estava registrado."
            )

            return

        if page is None:

            raise ValueError(
                "Não é possível registrar NetworkService "
                "porque a página Playwright é None."
            )

        page.on(
            "response",
            self._on_response
        )

        self._registered = True

        self.log.success(
            "NetworkService registrado."
        )

    # ==========================================================
    # Controle da captura
    # ==========================================================

    def start_capture(self):
        """
        Inicia uma nova sessão de captura.
        """

        with self._lock:

            self._responses.clear()

            self._capturing = True

        self.log.info(
            "Captura iniciada."
        )

    def stop_capture(self):
        """
        Finaliza a captura.
        """

        with self._lock:

            self._capturing = False

        self.log.info(
            "Captura encerrada."
        )

    # ==========================================================
    # Callback Playwright
    # ==========================================================

    def _on_response(
        self,
        response: Response
    ):
        """
        Processa cada resposta HTTP recebida pelo Playwright.
        """

        if not self._capturing:
            return

        try:

            url = response.url

            headers = response.headers

            content_type = headers.get(
                "content-type",
                ""
            ).lower()

            content_length = headers.get(
                "content-length",
                "?"
            )

            # ==================================================
            # DIAGNÓSTICO DA REDE
            # ==================================================

            self.log.info(
                "NETWORK RESPONSE"
            )

            self.log.info(
                f"Status : {response.status}"
            )

            self.log.info(
                f"Mime   : {content_type}"
            )

            self.log.info(
                f"Size   : {content_length}"
            )

            self.log.info(
                f"URL    : {url}"
            )

            # ==================================================
            # FILTRO DE URL
            # ==================================================

            if self.is_invalid_url(url, content_type):

                self.log.debug(
                    f"URL ignorada: {url[:150]}"
                )

                return

            # ==================================================
            # FILTRO DE MÍDIA
            # ==================================================

            if not self.is_media_response(
                url,
                content_type
            ):

                self.log.debug(
                    f"Resposta não é mídia: {url[:150]}"
                )

                return

            # ==================================================
            # CAPTURA DO BINÁRIO
            # ==================================================

            normalized_url = (url or "").lower()

            body = response.body()

            if not body:

                self.log.debug(
                    f"Resposta sem conteúdo: {url[:150]}"
                )

                return

            size = len(body)

            if normalized_url.startswith("blob:"):
                self.log.warning(
                    "BLOB DE MÍDIA DETECTADO | "
                    f"Mime={content_type} | "
                    f"Size={size:,}"
                )

            self.log.info(
                "BODY CAPTURED | "
                f"header_size={content_length} | "
                f"body_size={size:,} | "
                f"url={url}"
            )

            self.log.info(
                f"Body   : {size:,} bytes"
            )

            # ==================================================
            # RESTANTE DO SEU CÓDIGO
            # ==================================================

            if size < self.MIN_MEDIA_SIZE:

                self.log.debug(
                    f"Resposta pequena ignorada: "
                    f"{size:,} bytes | {url[:150]}"
                )

                return

            media_type = self.detect_type(
                url=url,
                mime=content_type
            )

            info = {

                "type": media_type,

                "url": url,

                "status": response.status,

                "headers": headers,

                "mime": content_type,

                "size": size,

                "data": body,

            }

            with self._lock:

                self._responses.append(
                    info
                )

            self.log.success(
                f"Mídia HTTP capturada: "
                f"{size:,} bytes"
            )

            self.log.info(
                f"Tipo : {media_type}"
            )

            self.log.info(
                f"Mime : {content_type}"
            )

            self.log.info(
                f"URL  : {url}"
            )

        except Exception as error:

            self.log.error(
                "Erro ao processar resposta da rede: "
                f"{error}"
            )

            if url:
                self.log.error(
                    f"URL da resposta com erro: {url[:300]}"
                )


    # ==========================================================
    # Validação da URL
    # ==========================================================

    def is_invalid_url(
        self,
        url: str,
        content_type: str = ""
    ) -> bool:
        """
        Determina se a URL deve ser descartada.

        URLs blob: são aceitas quando representam
        imagens ou vídeos reais, pois o WhatsApp
        pode disponibilizar a mídia original dessa forma.
        """

        if not url:
            return True

        normalized = url.lower()

        normalized_mime = (
            content_type or ""
        ).lower()

        # ==================================================
        # BLOB
        # ==================================================

        if normalized.startswith("blob:"):

            if (
                normalized_mime.startswith("image/")
                or normalized_mime.startswith("video/")
            ):
                return False

            return True

        # ==================================================
        # DEMAIS URLs INVÁLIDAS
        # ==================================================

        for marker in self.INVALID_URL_MARKERS:

            if marker == "blob:":
                continue

            if marker in normalized:

                return True

        return False
    # ==========================================================
    # Filtro de mídia
    # ==========================================================

    def is_media_response(
        self,
        url: str,
        content_type: str
    ) -> bool:
        """
        Determina se uma resposta HTTP representa uma mídia.
        """

        normalized_url = (
            url or ""
        ).lower()

        normalized_mime = (
            content_type or ""
        ).lower()

        #
        # Content-Type é a primeira prioridade.
        #

        if normalized_mime.startswith(
            "image/"
        ):

            return True

        if normalized_mime.startswith(
            "video/"
        ):

            return True

        #
        # Extensões conhecidas.
        #

        media_extensions = (

            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".mp4",
            ".webm",
            ".mov",

        )

        if any(
            extension in normalized_url
            for extension in media_extensions
        ):

            return True

        #
        # Domínios conhecidos do WhatsApp.
        #

        for domain in self.MEDIA_DOMAINS:

            if domain in normalized_url:

                return True

        return False

    # ==========================================================
    # Thumbnail
    # ==========================================================

    def is_thumbnail_url(
        self,
        url: str
    ) -> bool:
        """
        Identifica URLs conhecidas de thumbnails.
        """

        normalized = (
            url or ""
        ).lower()

        for marker in self.THUMBNAIL_MARKERS:

            if marker in normalized:

                return True

        return False

    # ==========================================================
    # Detectar tipo
    # ==========================================================

    def detect_type(
        self,
        url: str,
        mime: str
    ) -> str:
        """
        Determina se a mídia é imagem ou vídeo.
        """

        normalized_mime = (
            mime or ""
        ).lower()

        normalized_url = (
            url or ""
        ).lower()

        #
        # MIME.
        #

        if normalized_mime.startswith(
            "image/"
        ):

            return "image"

        if normalized_mime.startswith(
            "video/"
        ):

            return "video"

        #
        # Extensão.
        #

        image_extensions = (

            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",

        )

        video_extensions = (

            ".mp4",
            ".webm",
            ".mov",

        )

        if any(
            extension in normalized_url
            for extension in image_extensions
        ):

            return "image"

        if any(
            extension in normalized_url
            for extension in video_extensions
        ):

            return "video"

        return "unknown"

    # ==========================================================
    # Melhor mídia
    # ==========================================================

    def get_best_media(self):
        """
        Retorna a melhor mídia capturada.

        Critérios:

        1. URL deve ser válida;
        2. não pode ser thumbnail;
        3. precisa possuir data;
        4. precisa possuir tamanho mínimo;
        5. precisa ser imagem ou vídeo;
        6. prioriza o maior conteúdo.

        Uma URL blob: pode ser retornada quando o registro possui
        os bytes reais em "data". Nesse caso o DownloaderService
        deve priorizar o conteúdo binário capturado.

        Retorno:

        {
            "type": "image",
            "url": "...",
            "status": 200,
            "headers": {...},
            "mime": "image/jpeg",
            "size": 1425246,
            "data": b"..."
        }
        """

        with self._lock:

            if not self._responses:

                self.log.warning(
                    "Nenhuma resposta capturada."
                )

                return None

            valid_medias = []

            for media in self._responses:

                url = media.get(
                    "url",
                    ""
                )

                size = media.get(
                    "size",
                    0
                )

                data = media.get(
                    "data"
                )

                media_type = media.get(
                    "type",
                    "unknown"
                )

                #
                # URL inválida.
                #

                if self.is_invalid_url(
                    url,
                    media.get("mime", "")
                ):
                    continue

                #
                # Thumbnail.
                #

                if self.is_thumbnail_url(url):

                    continue

                #
                # Sem dados binários.
                #

                if not data:

                    continue

                #
                # Tamanho mínimo.
                #

                if size < self.MIN_MEDIA_SIZE:

                    continue

                #
                # Tipo válido.
                #

                if media_type not in (
                    "image",
                    "video",
                ):

                    continue

                valid_medias.append(
                    media
                )

            #
            # Nenhuma mídia válida.
            #

            if not valid_medias:

                self.log.warning(
                    "Nenhuma mídia válida encontrada "
                    "pelo NetworkService."
                )

                return None

            #
            # Seleciona a maior mídia.
            #

            selected = max(
                valid_medias,
                key=lambda media: media.get(
                    "size",
                    0
                )
            )

        #
        # Logging fora do lock.
        #

        self.log.success(
            "Melhor mídia selecionada."
        )

        self.log.info(
            f"Tipo : {selected.get('type')}"
        )

        self.log.info(
            f"Mime : {selected.get('mime')}"
        )

        self.log.info(
            f"Tamanho : "
            f"{selected.get('size', 0):,} bytes"
        )

        self.log.info(
            f"URL : "
            f"{selected.get('url')}"
        )

        return selected

    # ==========================================================
    # Última mídia
    # ==========================================================

    def get_last_media(self):
        """
        Mantido para compatibilidade.

        Retorna a melhor mídia válida.
        """

        return self.get_best_media()

    # ==========================================================
    # Todas as mídias
    # ==========================================================

    def get_all_medias(self):

        with self._lock:

            return list(
                self._responses
            )

    # ==========================================================
    # Total
    # ==========================================================

    def total(self):

        with self._lock:

            return len(
                self._responses
            )

    # ==========================================================
    # Limpar
    # ==========================================================

    def clear(self):

        with self._lock:

            self._responses.clear()

        self.log.debug(
            "Respostas do NetworkService limpas."
        )

    # ==========================================================
    # Resumo
    # ==========================================================

    def print_summary(self):

        self.log.info(
            "Resumo das mídias capturadas"
        )

        medias = self.get_all_medias()

        if not medias:

            self.log.info(
                "Nenhuma mídia capturada."
            )

            return

        for index, media in enumerate(
            medias
        ):

            size = media.get(
                "size",
                0
            )

            mime = media.get(
                "mime",
                ""
            )

            media_type = media.get(
                "type",
                "unknown"
            )

            url = media.get(
                "url",
                ""
            )

            self.log.info(
                f"[{index}] "
                f"Tipo={media_type} | "
                f"Mime={mime} | "
                f"Tamanho={size:,} bytes"
            )

            self.log.info(
                f"URL: {url}"
            )