"""
ProjetoWhatsApp

Ponto de entrada da aplicação.
"""

from config import settings
from services.application import Application


def main() -> None:

    app = Application(settings)

    app.run()


if __name__ == "__main__":

    main()