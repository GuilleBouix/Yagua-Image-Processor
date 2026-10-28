"""Enlaces oficiales del proyecto compartidos por Inicio y la barra lateral."""

import webbrowser

from app.translations import get_language


WEBSITE_URL = 'https://yagua.bouixdev.workers.dev'


def open_project_page(*, documentation=False):
    """Use Spanish or English, the two languages available on the website."""
    language = 'es' if get_language() == 'Español' else 'en'
    section = 'docs/' if documentation else ''
    webbrowser.open(f'{WEBSITE_URL}/{language}/{section}')
