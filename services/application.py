"""
ProjetoWhatsApp

Orquestrador principal da aplicação.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from config import Settings

from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.login_service import LoginService
from services.conversation_service import ConversationService
from services.gallery_service import GalleryService
from services.viewer_service import ViewerService
from services.logger_service import LoggerService
from services.downloader_service import DownloaderService


class Application:
    """
    Classe responsável por controlar
    o ciclo de vida da aplicação.
    """

    def __init__(
        self,
        settings: Settings
    ) -> None:

        self.settings = settings

        LoggerService.configure()

        self.log = LoggerService.app()

        # Serviços
        self.database = DatabaseService()
        self.browser = BrowserService()

        self.login = LoginService(self.browser)
        self.conversation = ConversationService(self.browser)
        self.gallery = GalleryService(self.browser)
        self.viewer = ViewerService(self.browser)
        self.downloader = DownloaderService()

    # ======================================================
    # Execução principal
    # ======================================================

    def run(self) -> None:

        self.log.info("Inicializando aplicação...")

        try:

            self.initialize()
            self.execute()
            self.finish()

        except KeyboardInterrupt:

            self.log.warning("Execução interrompida pelo usuário.")

        except Exception:

            LoggerService.error().exception(
                "Erro inesperado na execução."
            )

        finally:

            self.shutdown()

    # ======================================================
    # Inicialização
    # ======================================================

    def initialize(self) -> None:

        self.log.info("Inicializando banco...")
        self.database.initialize()

    # ======================================================
    # Fluxo principal
    # ======================================================

    def execute(self) -> None:

        # ---------- Navegador ----------
        self.browser.start()
        self.browser.open_whatsapp()

        # ---------- Login ----------
        self.login.execute()

        # ---------- Abrir conversa ----------
        self.conversation.execute(
            self.settings.CONVERSATION_NAME
        )

        # ---------- Galeria ----------
        medias = self.gallery.execute()

        self.log.success(f"{len(medias)} mídias encontradas.")

        if not medias:

            self.log.warning("Nenhuma mídia para processar.")
            return

        # ---------- LOOP ----------
        success_count     = 0
        duplicate_count   = 0
        skipped_count     = 0
        failed_count      = 0

        total = len(medias)

        for idx, card_data in enumerate(medias, start=1):

            self.log.info(f"[{idx}/{total}] Processando mídia...")

            try:

                # 1) Capturar mídia
                media_object = self.viewer.test_media(
                    index=card_data["index"]
                )

            except Exception as e:

                self.log.warning(f"Falha ao capturar: {e}")

                try:
                    self.viewer.close_viewer()
                except Exception:
                    pass

                failed_count += 1
                continue

            if not media_object:

                self.log.warning("Mídia inválida. Pulando.")

                try:
                    self.viewer.close_viewer()
                except Exception:
                    pass

                skipped_count += 1
                continue

            # 2) Calcular SHA256 dos bytes (antes de salvar)
            data = media_object.get("data")
            sha256 = None

            if data:

                sha256 = self.downloader.sha256_bytes(data)

            # 3) Verificar duplicidade no banco
            if sha256 and self.database.exists_sha(sha256):

                self.log.warning(
                    f"SHA256 já existe: {sha256[:16]}... "
                    "Pulando download."
                )

                try:
                    self.viewer.close_viewer()
                except Exception:
                    pass

                duplicate_count += 1
                continue

            # 4) Baixar (agora o downloader também verifica phash)
            path = self.downloader.download(media_object)

            if not path:

                self.log.warning(
                    "Download ignorado (duplicado perceptual ou erro)."
                )

                try:
                    self.viewer.close_viewer()
                except Exception:
                    pass

                duplicate_count += 1
                continue

            # 5) Registrar no banco
            try:

                original_name = (
                    card_data.get("label")
                    or media_object.get("url", "unknown")
                )

                file_size = path.stat().st_size

                self.database.insert_media(
                    media_type    = media_object.get("type", "image"),
                    file_name     = path.name,
                    original_name = original_name,
                    extension     = media_object.get("extension", "jpg"),
                    conversation  = self.settings.CONVERSATION_NAME,
                    sha256        = sha256 or self.downloader.sha256_file(path),
                    local_path    = str(path),
                    file_size     = file_size,
                    downloaded    = 1,
                )

                self.log.success(
                    f"Mídia registrada no banco: {path.name}"
                )

                success_count += 1

            except Exception as e:

                self.log.error(f"Erro ao registrar no banco: {e}")

                LoggerService.error().exception("Detalhes do erro:")

                # NÃO deleta o arquivo, para preservar diagnóstico

                failed_count += 1

            # 6) Fechar visualizador
            try:
                self.viewer.close_viewer()
            except Exception:
                pass

        # ---------- Sincronizar pasta → banco ----------
        self._sync_folder_to_database()

        self.log.success(
            f"Resultado: {success_count} baixadas | "
            f"{duplicate_count} duplicadas | "
            f"{skipped_count} puladas | "
            f"{failed_count} erros."
        )

    # ======================================================
    # Varre a pasta downloads e registra no banco o que falta
    # ======================================================

    def _sync_folder_to_database(self) -> None:

        self.log.info(
            "Verificando pasta downloads ↔ banco de dados..."
        )

        folder = self.downloader.folder

        if not folder.exists():

            self.log.warning("Pasta downloads não existe.")
            return

        arquivos = [
            f for f in folder.iterdir()
            if f.is_file()
            and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".avi", ".mov"}
        ]

        self.log.info(f"Arquivos na pasta: {len(arquivos)}")

        registrados = 0
        duplicados  = 0

        for caminho in arquivos:

            try:

                sha = self.downloader.sha256_file(caminho)

            except Exception as e:

                self.log.warning(f"Falha ao ler hash de {caminho.name}: {e}")
                continue

            if self.database.exists_sha(sha):

                duplicados += 1
                continue

            # Não está no banco – registrar
            try:

                self.database.insert_media(
                    media_type = self._detect_type_from_path(caminho),
                    file_name  = caminho.name,
                    original_name = caminho.name,
                    extension  = caminho.suffix.lstrip("."),
                    conversation = self.settings.CONVERSATION_NAME,
                    sha256     = sha,
                    local_path = str(caminho),
                    file_size  = caminho.stat().st_size,
                    downloaded = 1,
                )

                self.log.success(
                    f"Arquivo registrado no banco: {caminho.name}"
                )

                registrados += 1

            except Exception as e:

                self.log.error(
                    f"Falha ao registrar {caminho.name}: {e}"
                )

        self.log.success(
            f"Sincronização concluída: {registrados} novos, "
            f"{duplicados} já existiam."
        )

    # ======================================================
    # Detectar tipo a partir da extensão
    # ======================================================

    @staticmethod
    def _detect_type_from_path(path: Path) -> str:

        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:

            return "image"

        if path.suffix.lower() in {".mp4", ".avi", ".mov"}:

            return "video"

        return "unknown"

    # ======================================================
    # Finalização
    # ======================================================

    def finish(self) -> None:

        self.log.success("Processamento finalizado.")

    def shutdown(self) -> None:

        try:
            self.database.disconnect()
        except Exception:
            pass

        try:
            self.browser.stop()
        except Exception:
            pass

        self.log.info("Aplicação encerrada.")