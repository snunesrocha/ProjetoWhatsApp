from pathlib import Path
from playwright.sync_api import sync_playwright
from config import SESSION_DIR, HEADLESS


class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.context = None

    def start(self):

        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        self.playwright = sync_playwright().start()

        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=HEADLESS,
            accept_downloads=True,
            viewport={"width": 1400, "height": 900},
        )

        return self.context

    def stop(self):

        if self.context:
            self.context.close()

        if self.playwright:
            self.playwright.stop()