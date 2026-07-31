"""
ProjetoWhatsApp

Configuração central da aplicação.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    #
    # Aplicação
    #
    APP_NAME: str = "ProjetoWhatsApp"
    APP_VERSION: str = "1.0.0"

    #
    # Browser
    #
    HEADLESS: bool = False
    SLOW_MO: int = 300
    TIMEOUT: int = 30000

    #
    # WhatsApp
    #
    CONVERSATION_NAME: str

    #
    # Pastas
    #
    DOWNLOAD_PATH: Path = Field(default=Path("downloads"))
    PHOTO_FOLDER: str = "photos"
    VIDEO_FOLDER: str = "videos"

    DATABASE_PATH: Path = Field(default=Path("database/downloads.db"))
    SESSION_PATH: Path = Field(default=Path("session"))

    #
    # Logs
    #
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "20 MB"
    LOG_RETENTION: str = "30 days"
    LOG_COMPRESSION: str = "zip"

    #
    # Download
    #
    MAX_RETRY: int = 3
    WAIT_AFTER_DOWNLOAD: float = 1.5
    WAIT_AFTER_NEXT: float = 0.4

    @property
    def PHOTO_PATH(self) -> Path:
        return self.DOWNLOAD_PATH / self.PHOTO_FOLDER

    @property
    def VIDEO_PATH(self) -> Path:
        return self.DOWNLOAD_PATH / self.VIDEO_FOLDER

    def create_directories(self) -> None:
        """
        Cria automaticamente toda a estrutura de diretórios.
        """

        self.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

        self.PHOTO_PATH.mkdir(parents=True, exist_ok=True)

        self.VIDEO_PATH.mkdir(parents=True, exist_ok=True)

        self.DATABASE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.SESSION_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )


settings = Settings()

settings.create_directories()