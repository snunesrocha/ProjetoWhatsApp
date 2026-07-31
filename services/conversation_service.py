from services.locators import WhatsAppLocators
from playwright.sync_api import TimeoutError


class ConversationService:


    def open_conversation(self, page, name):

        print(f"\nProcurando conversa: {name}")


        try:

            search = page.locator(
                WhatsAppLocators.SEARCH_BOX
            )

            search.wait_for(
                state="visible",
                timeout=15000
            )

            search.click()

            search.fill(name)

            page.wait_for_timeout(3000)


        except TimeoutError:

            print("❌ Caixa de pesquisa não encontrada")
            return False


        print("\nResultados encontrados:")
        print("----------------------")


        titles = page.locator("[title]")

        encontrados = []


        for i in range(titles.count()):

            title = titles.nth(i).get_attribute("title")

            if title and name.lower() in title.lower():

                encontrados.append(title)


        for item in encontrados:

            print(item)


        if not encontrados:

            print("\n❌ Nenhuma conversa encontrada")

            return False


        try:

            chat = page.locator(
                f"[title*='{name}']"
            ).first


            chat.click()


            print("\n✅ Conversa aberta")

            return True


        except Exception as e:

            print("\n❌ Erro ao abrir conversa:")
            print(e)

            return False