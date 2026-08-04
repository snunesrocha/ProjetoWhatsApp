"""
ProjetoWhatsApp

Serviço responsável pelo gerenciamento do navegador.
"""

from __future__ import annotations

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    BrowserContext,
    Page,
)

from config import settings
from constants.app_constants import AppConstants
from services.logger_service import LoggerService
from services.network_service import NetworkService

class BrowserService:
    """
    Gerencia o Playwright, o BrowserContext e a Page.
    """

    def __init__(self):

        self.log = LoggerService.app()

        self._playwright: Playwright | None = None

        self._context: BrowserContext | None = None

        self._page: Page | None = None

        self.network = NetworkService()



    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def playwright(self) -> Playwright:

        return self._playwright

    @property
    def context(self) -> BrowserContext:

        return self._context

    @property
    def current_page(self) -> Page:

        return self._page

    # ==========================================================
    # Inicialização
    # ==========================================================

    def start(self) -> None:

        self.log.info("Inicializando Playwright...")

        self._playwright = sync_playwright().start()

        self.log.info("Abrindo Chromium...")

        self._context = (
            self._playwright.chromium.launch_persistent_context(

                user_data_dir=str(settings.SESSION_PATH),

                headless=settings.HEADLESS,

                slow_mo=settings.SLOW_MO,

                accept_downloads=True,
            )
        )

        #
        # Página
        #
        if self._context.pages:

            self._page = self._context.pages[0]

        else:

            self._page = self._context.new_page()

        #
        # Agora a página existe
        #

        self.network.register(self._page)

        self._page.set_default_timeout(

            settings.TIMEOUT

        )

        self.log.success("Chromium iniciado.")

    # ==========================================================
    # Navegação
    # ==========================================================

    def open_whatsapp(self) -> None:

        self.log.info("Abrindo WhatsApp Web...")

        self._page.goto(

            AppConstants.WHATSAPP_WEB,

            wait_until="domcontentloaded",

        )

        self.log.success("WhatsApp aberto.")

    # ==========================================================
    # Utilidades
    # ==========================================================

    def wait_load(self) -> None:

        self._page.wait_for_load_state("networkidle")

    def screenshot(self, filename: str) -> None:

        self._page.screenshot(path=filename)

    # ==========================================================
    # Encerramento
    # ==========================================================

    def stop(self) -> None:

        self.log.info("Encerrando navegador...")

        try:

            if self._context:

                self._context.close()

        finally:

            if self._playwright:

                self._playwright.stop()

        self.log.success("Navegador encerrado.")