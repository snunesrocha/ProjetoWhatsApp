"""
ProjetoWhatsApp

Responsável por salvar mídias baixadas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import hashlib
import uuid
import time

from PIL import Image
import imagehash

from services.logger_service import LoggerService


class DownloaderService:

    def __init__(self) -> None:

        self.log = LoggerService.app()

        self.folder = Path("downloads")

        self.folder.mkdir(exist_ok=True)

    # ==========================================================
    # Gera SHA256 a partir de bytes
    # ==========================================================

    @staticmethod
    def sha256_bytes(data: bytes) -> str:

        return hashlib.sha256(data).hexdigest()

    # ==========================================================
    # Gera SHA256 a partir de arquivo
    # ==========================================================

    @staticmethod
    def sha256_file(filepath: Path) -> str:

        sha256 = hashlib.sha256()

        with open(filepath, "rb") as f:

            for chunk in iter(lambda: f.read(8192), b""):

                sha256.update(chunk)

        return sha256.hexdigest()

    # ==========================================================
    # Compara duas imagens por hash perceptual
    # ==========================================================

    @staticmethod
    def compare_images(
        img1_path: Path,
        img2_path: Path,
        limiar: int = 5
    ) -> bool:
        """
        Retorna True se as imagens forem semelhantes
        (diferença perceptual <= limiar).
        """

        try:

            img1 = Image.open(img1_path)

            img2 = Image.open(img2_path)

            hash1 = imagehash.phash(img1)

            hash2 = imagehash.phash(img2)

            diferenca = hash1 - hash2

            return diferenca <= limiar

        except Exception as e:

            LoggerService.debug().debug(
                f"Erro ao comparar imagens: {e}"
            )

            return False

    # ==========================================================
    # Verifica se já existe imagem perceptual igual na pasta
    # ==========================================================

    def find_duplicate_phash(
        self,
        file_path: Path,
        limiar: int = 5
    ) -> Optional[Path]:
        """
        Procura na pasta de downloads uma imagem que seja
        perceptualmente idêntica a `file_path`.

        Retorna o caminho do arquivo duplicado, ou None.
        """

        if not file_path.exists():

            return None

        # Apenas imagens
        extensoes = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

        if file_path.suffix.lower() not in extensoes:

            return None

        for item in self.folder.iterdir():

            if item.is_file() and item.suffix.lower() in extensoes:

                # Não comparar com ele mesmo
                if item.resolve() == file_path.resolve():

                    continue

                if self.compare_images(
                    file_path,
                    item,
                    limiar
                ):

                    return item

        return None

    # ==========================================================
    # Baixa mídia (com validação de duplicidade)
    # ==========================================================

    def download(self, media: dict) -> Path | None:
        """
        media deve conter:
            - 'data' (bytes)
            - 'extension' (str)
            - 'type' (str) opcional

        Retorna o caminho salvo, ou None se for duplicado.
        """

        if not media:

            self.log.warning("Nenhuma mídia para salvar.")
            return None

        data = media.get("data")

        if not data or not isinstance(data, (bytes, bytearray)):

            self.log.error("Campo 'data' ausente ou inválido.")
            return None

        # 1) Calcular SHA256 dos bytes
        sha256 = self.sha256_bytes(data)

        # 2) Verificar duplicidade no banco (via callback)
        #    O Application passará o DatabaseService?
        #    Aqui apenas preparamos o hash; a checagem é feita
        #    no Application para não acoplar serviços.
        #    Por isso, retornamos None se o hash for None.

        if not sha256:

            return None

        # 3) Gerar nome único
        timestamp = int(time.time() * 1000)

        rand = uuid.uuid4().hex[:8]

        ext = media.get("extension", "jpg")

        filename = f"whatsapp_{timestamp}_{rand}.{ext}"

        filepath = self.folder / filename

        # 4) Salvar temporariamente para comparar phash
        try:

            with open(filepath, "wb") as f:

                f.write(data)

            # 5) Verificar duplicidade perceptual
            dup = self.find_duplicate_phash(filepath)

            if dup:

                self.log.warning(
                    f"Imagem já baixada anteriormente: {dup.name}"
                )

                # Remove o arquivo recém-salvo
                self._delete(filepath)

                return None

            self.log.success(f"Mídia salva: {filepath}")

            return filepath

        except Exception as e:

            self.log.error(f"Erro ao salvar mídia: {e}")

            self._delete(filepath)

            return None

    # ==========================================================
    # Remove arquivo silenciosamente
    # ==========================================================

    @staticmethod
    def _delete(filepath: Path) -> None:

        try:

            filepath.unlink(missing_ok=True)

        except Exception:

            pass
        