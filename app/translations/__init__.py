"""
Sistema de traducciones multiidioma.
Provee funciÃ³n t() para obtener textos traducidos.
"""

from typing import Optional
import json
from pathlib import Path

# Idiomas disponibles
AVAILABLE_LANGUAGES = {
    'EspaÃ±ol': 'EspaÃ±ol',
    'English': 'English',
    'PortuguÃªs': 'PortuguÃªs',
}

# Idioma por defecto
DEFAULT_LANGUAGE = 'English'

# Idioma actual (se carga desde settings)
_current_lang: Optional[str] = None


def _load_settings() -> dict:
    """Carga la configuraciÃ³n de usuario."""
    settings_path = Path(__file__).resolve().parents[1] / 'user_settings.json'
    if settings_path.exists():
        try:
            return json.loads(settings_path.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def _save_settings(settings: dict):
    """Guarda la configuraciÃ³n de usuario."""
    settings_path = Path(__file__).resolve().parents[1] / 'user_settings.json'
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


def get_language() -> str:
    """Obtiene el idioma actual."""
    global _current_lang
    if _current_lang is None:
        settings = _load_settings()
        _current_lang = settings.get('language') or DEFAULT_LANGUAGE
    return _current_lang


def set_language(lang: str):
    """Cambia el idioma y lo guarda en settings."""
    global _current_lang
    if lang in AVAILABLE_LANGUAGES:
        _current_lang = lang
        settings = _load_settings()
        settings['language'] = lang
        _save_settings(settings)


def get_translations(lang: Optional[str] = None) -> dict:
    """Carga las traducciones del idioma especificado."""
    if lang is None:
        lang = get_language()
    
    if lang == 'EspaÃ±ol':
        from app.translations.es import TRANSLATIONS
    elif lang == 'English':
        from app.translations.en import TRANSLATIONS
    elif lang == 'PortuguÃªs':
        from app.translations.pt import TRANSLATIONS
    else:
        from app.translations.en import TRANSLATIONS
    
    return TRANSLATIONS


def t(key: str, lang: Optional[str] = None) -> str:
    """
    Obtiene la traducciÃ³n para una clave.
    
    Args:
        key: Clave de traducciÃ³n (ej: 'compress_title')
        lang: Idioma opcional (usa el actual si no se especifica)
    
    Returns:
        Texto traducido o la clave si no se encuentra
    """
    translations = get_translations(lang)
    return translations.get(key, key)
