"""
ProjetoWhatsApp

Responsável por salvar mídias baixadas.
"""

from pathlib import Path

from services.logger_service import LoggerService



class DownloaderService:


    def __init__(self):


        self.log = LoggerService.app()


        self.folder = Path(
            "downloads"
        )


        self.folder.mkdir(
            exist_ok=True
        )



    def download(
        self,
        media
    ):


        if not media:


            self.log.warning(
                "Nenhuma mídia para salvar."
            )

            return None



        filename = (

            "whatsapp_media."

            + media.get(
                "extension",
                "jpg"
            )

        )



        path = self.folder / filename



        with open(
            path,
            "wb"
        ) as file:


            file.write(
                media["data"]
            )



        self.log.success(
            f"Mídia salva: {path}"
        )


        return path