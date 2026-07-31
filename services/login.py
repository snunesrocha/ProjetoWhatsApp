from playwright.sync_api import TimeoutError


class LoginService:

    def login(self, page):

        page.goto("https://web.whatsapp.com")

        print()
        print("=" * 60)
        print("Aguardando login no WhatsApp...")
        print("=" * 60)

        try:

            page.wait_for_selector(
                "div[aria-label='Lista de conversas']",
                timeout=120000
            )

            print()
            print("Login realizado.")

        except TimeoutError:

            print("Tempo esgotado.")
            raise