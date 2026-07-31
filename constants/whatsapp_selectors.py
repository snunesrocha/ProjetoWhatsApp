"""
Seletores utilizados pelo WhatsApp Web.
"""


class WhatsAppSelectors:

    #
    # LOGIN
    #

    SEARCH_BOX = (
        "input[aria-label='Pesquisar ou começar uma nova conversa']"
    )

    QR_CODE = "canvas"

    #
    # CONVERSA
    #

    CONVERSATION_INFO = (
        '[data-testid="conversation-info-header"]'
    )

    SEARCH_RESULT = (
        '[data-testid="cell-frame-container"]'
    )

    #
    # MENU DA CONVERSA
    #

    MEDIA_LINKS_DOCS = (
        '[data-testid="block-media-links-docs"]'
    )

    #
    # GALERIA
    #

    MEDIA_TAB = (
        '[data-testid="gallery-tab-media"]'
    )

    GALLERY_GRID = (
        '[data-testid="media-gallery"]'
    )

    #
    # VISUALIZADOR
    #

    MEDIA_VIEWER = (
        '[data-testid="media-viewer-modal"]'
    )

    DOWNLOAD_BUTTON = (
        '[data-testid="media-viewer-modal"] >> role=button[name="Baixar"]'
    )

    NEXT_BUTTON = (
        'role=button[name="Avançar"]'
    )

    CLOSE_BUTTON = (
        'role=button[name="Fechar"]'
    )