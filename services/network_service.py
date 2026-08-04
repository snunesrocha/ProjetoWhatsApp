"""
ProjetoWhatsApp

Serviço responsável por interceptar as respostas HTTP
do WhatsApp Web.

Não realiza download.

Apenas captura as respostas da rede para que
o DownloaderService grave posteriormente.
"""

from __future__ import annotations

from threading import Lock

from playwright.sync_api import Response

from services.logger_service import LoggerService


class NetworkService:

    """
    Captura respostas HTTP contendo imagens ou vídeos.
    """

    def __init__(self):

        self.log = LoggerService.app()

        self._capturing = False

        self._responses = []

        self._lock = Lock()

        self._registered = False

    # =====================================================
    # Registro
    # =====================================================

    def register(self, page):

        """
        Deve ser chamado apenas uma vez.
        """

        if self._registered:
            return

        page.on(
            "response",
            self._on_response
        )

        self._registered = True

        self.log.success(
            "NetworkService registrado."
        )

    # =====================================================
    # Controle
    # =====================================================

    def start_capture(self):

        with self._lock:

            self._responses.clear()

            self._capturing = True

        self.log.info(
            "Captura iniciada."
        )

    def stop_capture(self):

        with self._lock:

            self._capturing = False

        self.log.info(
            "Captura encerrada."
        )

    # =====================================================
    # Callback Playwright
    # =====================================================

    def _on_response(
        self,
        response: Response
    ):

        if not self._capturing:
            return

        try:

            url = response.url

            headers = response.headers

            content_type = headers.get(
                "content-type",
                ""
            ).lower()

            if not self.is_media_response(
                url,
                content_type
            ):
                return

            body = response.body()

            #
            # Ignora miniaturas muito pequenas
            #

            if len(body) < 15000:

                return


            #
            # determina o tipo
            #

            media_type = "unknown"

            if content_type.startswith("image/"):

                media_type = "image"

            elif content_type.startswith("video/"):

                media_type = "video"

            elif ".jpg" in url.lower() or ".jpeg" in url.lower() or ".png" in url.lower():

                media_type = "image"

            elif ".mp4" in url.lower():

                media_type = "video"


            info = {

                "type": media_type,

                "url": url,

                "status": response.status,

                "headers": headers,

                "mime": content_type,

                "size": len(body),

                "data": body

            }


            with self._lock:

                self._responses.append(
                    info
                )

            self.log.success(

                f"Mídia capturada: {len(body):,} bytes"

            )

            self.log.info(

                f"{url}"

            )

        except Exception as error:

            self.log.debug(

                f"Resposta ignorada: {error}"

            )

    # =====================================================
    # Filtro
    # =====================================================

    def is_media_response(
        self,
        url: str,
        content_type: str
    ) -> bool:

        #
        # imagens
        #

        if content_type.startswith("image/"):
            return True

        #
        # vídeos
        #

        if content_type.startswith("video/"):
            return True

        #
        # alguns servidores não enviam
        # content-type corretamente
        #

        domains = [

            "cdn.whatsapp.net",

            "mmg.whatsapp.net",

            "media.",

            "lookaside"

        ]

        for item in domains:

            if item in url:

                return True

        return False

    # =====================================================
    # Consulta
    # =====================================================

    def get_last_media(self):

        with self._lock:

            if not self._responses:

                return None

            #
            # retorna sempre a maior mídia capturada
            #

            return max(

                self._responses,

                key=lambda media: media["size"]

            )

    # =====================================================
    # Melhor mídia capturada
    # =====================================================

    def get_best_media(self):

        with self._lock:

            if not self._responses:
                return None

            medias = sorted(

                self._responses,

                key=lambda x: x["size"],

                reverse=True

            )

            #
            # prioriza imagens/vídeos grandes
            #

            for media in medias:

                url = media["url"]

                if "dst-jpg_s96" in url:
                    continue

                if "dst-jpg_s64" in url:
                    continue

                if media["size"] < 50000:
                    continue

                return media

            #
            # fallback
            #

            return medias[0]
    

    def get_all_medias(self):

        with self._lock:

            return list(
                self._responses
            )

    def total(self):

        with self._lock:

            return len(
                self._responses
            )

    def clear(self):

        with self._lock:

            self._responses.clear()

    # =====================================================
    # Debug
    # =====================================================

    def print_summary(self):

        self.log.info(
            "Resumo das mídias capturadas"
        )

        for i, media in enumerate(self.get_all_medias()):

            self.log.info(

                f"[{i}] "

                f"{media['size']:,} bytes "

                f"{media['mime']}"

            )

            self.log.info(

                media["url"]

            )