"""
ProjetoWhatsApp

Serviço responsável pela configuração centralizada dos logs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

from loguru import logger


class LoggerService:
    """
    Serviço responsável pela configuração dos logs.
    """

    _configured = False

    _app_logger = None
    _download_logger = None
    _debug_logger = None
    _error_logger = None

    _execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    _log_folder = Path("logs") / _execution_id

    @classmethod
    def configure(cls) -> None:

        if cls._configured:
            return

        cls._log_folder.mkdir(parents=True, exist_ok=True)

        logger.remove()

        #
        # Console
        #
        logger.add(
            sys.stderr,
            level="INFO",
            colorize=True,
            backtrace=False,
            diagnose=False,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{message}</cyan>"
            ),
        )

        #
        # Application
        #
        logger.add(
            cls._log_folder / "application.log",
            level="INFO",
            encoding="utf-8",
            rotation="20 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
            filter=lambda r: r["extra"].get("log_type") == "application",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{module}:{function}:{line} | "
                "{message}"
            ),
        )

        #
        # Download
        #
        logger.add(
            cls._log_folder / "download.log",
            level="INFO",
            encoding="utf-8",
            rotation="20 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
            filter=lambda r: r["extra"].get("log_type") == "download",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{message}"
            ),
        )

        #
        # Debug
        #
        logger.add(
            cls._log_folder / "debug.log",
            level="DEBUG",
            encoding="utf-8",
            rotation="20 MB",
            retention="15 days",
            compression="zip",
            enqueue=True,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{module}:{function}:{line} | "
                "{message}"
            ),
        )

        #
        # Errors
        #
        logger.add(
            cls._log_folder / "errors.log",
            level="ERROR",
            encoding="utf-8",
            rotation="20 MB",
            retention="90 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{module}:{function}:{line}\n"
                "{message}\n"
            ),
        )

        cls._app_logger = logger.bind(log_type="application")

        cls._download_logger = logger.bind(log_type="download")

        cls._debug_logger = logger

        cls._error_logger = logger

        cls._configured = True

        cls._app_logger.success(
            f"Logger inicializado. Pasta: {cls._log_folder}"
        )

    @classmethod
    def app(cls):

        return cls._app_logger

    @classmethod
    def download(cls):

        return cls._download_logger

    @classmethod
    def debug(cls):

        return cls._debug_logger

    @classmethod
    def error(cls):

        return cls._error_logger

    @classmethod
    def execution_id(cls):

        return cls._execution_id

    @classmethod
    def log_folder(cls):

        return cls._log_folder