"""Enlaces públicos de apoyo al proyecto."""

from app.languages import LANGUAGE_MODULES
from app.translations import get_language


SUPPORT_URL_ES = "https://yagua.bouixdev.workers.dev/es/apoyar/"
SUPPORT_URL_EN = "https://yagua.bouixdev.workers.dev/en/support/"


def support_url() -> str:
    """Devuelve la página de apoyo en español o inglés según el idioma de Yagua."""
    language = LANGUAGE_MODULES.get(get_language(), "en")
    return SUPPORT_URL_ES if language == "es" else SUPPORT_URL_EN
