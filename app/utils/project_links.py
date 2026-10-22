"""Official project destinations shared by Home and the sidebar."""

import webbrowser

from app.translations import get_language


WEBSITE_URL = 'https://yagua.app'


def open_project_page(*, documentation=False):
    """Use Spanish or English, the two languages available on the website."""
    language = 'es' if get_language() == 'Español' else 'en'
    section = 'docs/' if documentation else ''
    webbrowser.open(f'{WEBSITE_URL}/{language}/{section}')
