"""
ProjetoWhatsApp

Serviço responsável pelo acesso ao banco SQLite.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from config import settings
from services.logger_service import LoggerService


class DatabaseService:

    def __init__(self) -> None:

        self.log = LoggerService.app()
        self.debug = LoggerService.debug()

        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    # ---------------------------------------------------------
    # Conecta ao banco
    # ---------------------------------------------------------

    def connect(self) -> None:

        if self.connection:
            return

        self.log.info("Conectando ao banco SQLite...")

        self.connection = sqlite3.connect(
            settings.DATABASE_PATH
        )

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        self.log.success("Banco conectado.")

    # ---------------------------------------------------------
    # Fecha conexão
    # ---------------------------------------------------------

    def disconnect(self) -> None:

        if self.connection:

            self.connection.close()

            self.connection = None
            self.cursor = None

            self.log.info("Banco encerrado.")

    # ---------------------------------------------------------
    # Inicializa tabelas
    # ---------------------------------------------------------

    def initialize(self) -> None:

        self.connect()

        self.log.info("Verificando estrutura do banco...")

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS media (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            media_type TEXT NOT NULL,

            file_name TEXT NOT NULL,

            original_name TEXT,

            extension TEXT,

            whatsapp_id TEXT,

            conversation TEXT,

            media_date TEXT,

            download_date TEXT,

            file_size INTEGER,

            sha256 TEXT,

            downloaded INTEGER DEFAULT 0,

            local_path TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP

        )

        """)

        self.cursor.execute("""

        CREATE UNIQUE INDEX IF NOT EXISTS idx_media_sha

        ON media(sha256)

        """)

        self.connection.commit()

        self.log.success("Estrutura do banco pronta.")

    # ---------------------------------------------------------
    # Executa INSERT / UPDATE / DELETE
    # ---------------------------------------------------------

    def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> None:

        self.cursor.execute(sql, params)

        self.connection.commit()

    # ---------------------------------------------------------
    # Retorna um registro
    # ---------------------------------------------------------

    def fetch_one(
        self,
        sql: str,
        params: tuple = ()
    ):

        self.cursor.execute(sql, params)

        return self.cursor.fetchone()

    # ---------------------------------------------------------
    # Retorna vários registros
    # ---------------------------------------------------------

    def fetch_all(
        self,
        sql: str,
        params: tuple = ()
    ):

        self.cursor.execute(sql, params)

        return self.cursor.fetchall()

    # ---------------------------------------------------------
    # Verifica se o hash já existe
    # ---------------------------------------------------------

    def exists_sha(
        self,
        sha256: str
    ) -> bool:

        row = self.fetch_one(

            """

            SELECT id

            FROM media

            WHERE sha256 = ?

            """,

            (sha256,)

        )

        return row is not None

    # ---------------------------------------------------------
    # Insere mídia
    # ---------------------------------------------------------

    def insert_media(
        self,
        media_type: str,
        file_name: str,
        original_name: str,
        extension: str,
        conversation: str,
        sha256: str,          # tipo forte (str)
        local_path: str,
        file_size: int,
        downloaded: int = 1
    ) -> None:

        if not sha256:
            raise ValueError(
                "SHA256 não pode ser nulo ou vazio. "
                "Repita a execução ou corrija o fluxo."
            )

        self.execute(
            """
            INSERT INTO media (
                media_type, file_name, original_name, extension,
                conversation, sha256, local_path, file_size,
                downloaded, download_date
            )
            VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
            """,
            (
                media_type, file_name, original_name, extension,
                conversation, sha256, local_path, file_size,
                downloaded,
            ),
        )
    # ---------------------------------------------------------
    # Estatísticas
    # ---------------------------------------------------------

    def total_downloads(self) -> int:

        row = self.fetch_one(

            """

            SELECT COUNT(*)

            FROM media

            WHERE downloaded = 1

            """

        )

        return row[0]

    # ---------------------------------------------------------
    # Total fotos
    # ---------------------------------------------------------

    def total_photos(self) -> int:

        row = self.fetch_one(

            """

            SELECT COUNT(*)

            FROM media

            WHERE media_type='photo'

            """

        )

        return row[0]

    # ---------------------------------------------------------
    # Total vídeos
    # ---------------------------------------------------------

    def total_videos(self) -> int:

        row = self.fetch_one(

            """

            SELECT COUNT(*)

            FROM media

            WHERE media_type='video'

            """

        )

        return row[0]