"""
Constantes da aplicação.
"""

from pathlib import Path


class AppConstants:

    # URLs
    WHATSAPP_WEB = "https://web.whatsapp.com"

    # Diretórios
    DOWNLOADS = Path("downloads")
    DATABASE = Path("database")
    LOGS = Path("logs")
    SESSION = Path("session")

    # Tipos de mídia
    PHOTO = "photo"
    VIDEO = "video"

    # Extensões suportadas
    IMAGE_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    )

    VIDEO_EXTENSIONS = (
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
    )