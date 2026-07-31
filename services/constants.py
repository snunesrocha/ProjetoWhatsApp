class WhatsAppSelectors:

    SEARCH_BOX = (
        "input[aria-label='Pesquisar ou começar uma nova conversa']"
    )

    CONVERSATION_HEADER = (
        '[data-testid="conversation-info-header"]'
    )

    MEDIA_TAB = (
        '[data-testid="gallery-tab-media"]'
    )

    MEDIA_VIEWER = (
        '[data-testid="media-viewer-modal"]'
    )

    DOWNLOAD_BUTTON = (
        '[data-testid="media-viewer-modal"] >> role=button[name="Baixar"]'
    )

    NEXT_BUTTON = (
        'role=button[name="Avançar"]'
    )