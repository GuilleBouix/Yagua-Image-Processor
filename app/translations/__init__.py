"""
Sistema de traducciones multiidioma.
Provee funcion t() para obtener textos traducidos.

Permite que la interfaz se muestre en diferentes idiomas segun
la preferencia del usuario guardada en user_settings.json.

Relacionado con:
    - app/app.py: Usa t() para el titulo de la ventana.
    - app/ui/sidebar.py: Usa t() para labels de menu.
    - app/ui/frames/*: Usa t() para todos los textos de UI.
    - app/translations/es.py: Traducciones al español.
    - app/translations/en.py: Traducciones al ingles.
    - app/translations/pt.py: Traducciones al portugues.
    - app/user_settings.json: Guarda el idioma seleccionado.
"""

from typing import Optional
from importlib import import_module

from app.utils.settings import settings_path, load_settings, save_settings
from app.languages import AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE, LANGUAGE_MODULES


# Idioma actual (se carga desde settings al inicio)
_current_lang: Optional[str] = None


def _load_settings() -> dict:
    """Carga preferencias tolerando archivos inválidos o estructuras no reconocidas."""
    return load_settings(settings_path())


def _save_settings(settings: dict) -> None:
    """Persiste preferencias sin impedir el uso de la interfaz si falla el disco."""
    save_settings(settings, settings_path())


def get_language():
    """
    Obtiene el idioma actual seleccionado.
    
    Si no hay idioma cargado, lo lee del archivo de settings.
    Si no hay settings, usa el idioma por defecto.
    
    Returns:
        Nombre del idioma actual (ej: 'Español', 'English', 'Portugues').
    """
    global _current_lang
    
    if _current_lang is None:
        settings = _load_settings()
        _current_lang = settings.get('language') or DEFAULT_LANGUAGE
    
    return _current_lang


def set_language(lang):
    """
    Cambia el idioma y lo guarda en settings.
    
    Actualiza el idioma global y persiste la eleccion en
    el archivo user_settings.json para que se mantenga
    entre sesiones.
    
    Args:
        lang: Nombre del idioma a establecer.
    """
    global _current_lang
    
    if lang in AVAILABLE_LANGUAGES:
        _current_lang = lang
        settings = _load_settings()
        settings['language'] = lang
        _save_settings(settings)


def get_translations(lang=None):
    """
    Carga las traducciones del idioma especificado.
    
    Si no se especifica idioma, usa el idioma actual.
    Importa dinamicamente el modulo de traducciones correspondiente.
    
    Args:
        lang: Nombre del idioma a cargar (o None para usar el actual).
        
    Returns:
        Diccionario con todas las traducciones del idioma.
    """
    if lang is None:
        lang = get_language()
    
    module = LANGUAGE_MODULES.get(lang, 'en')
    return import_module(f'app.translations.{module}').TRANSLATIONS


def t(key: str, lang: str | None = None) -> str:
    """
    Obtiene la traduccion para una clave.
    
    Esta es la funcion principal para obtener textos traducidos
    en toda la aplicacion.
    
    Args:
        key: Clave de traduccion (ej: 'compress_title', 'settings').
        lang: Idioma opcional (usa el actual si no se especifica).
        
    Returns:
        Texto traducido para la clave, o la clave misma si no se encuentra.
    """
    translations = get_translations(lang)
    return translations.get(key, key)
