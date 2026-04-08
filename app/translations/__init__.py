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
import json

from app.utils.settings import settings_path


# Idiomas disponibles en la aplicacion
AVAILABLE_LANGUAGES = {
    'Español': 'Español',
    'English': 'English',
    'Portugues': 'Portugues',
    'Français': 'Français',
}

# Idioma por defecto cuando no hay configuracion guardada
DEFAULT_LANGUAGE = 'Español'

# Idioma actual (se carga desde settings al inicio)
_current_lang: Optional[str] = None


def _load_settings():
    """
    Carga la configuracion de usuario desde el archivo JSON.
    
    Busca user_settings.json en el directorio raiz de la app
    y retorna las configuraciones guardadas.
    
    Returns:
        Diccionario con la configuracion o vacio si no existe.
    """
    # Construir ruta al archivo de settings
    path = settings_path()
    
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
    
    return {}


def _save_settings(settings):
    """
    Guarda la configuracion de usuario en el archivo JSON.
    
    Args:
        settings: Diccionario con la configuracion a guardar.
    """
    path = settings_path()
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


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
    
    # Importar el modulo de traducciones correspondiente
    if lang == 'Español':
        from app.translations.es import TRANSLATIONS
    elif lang == 'English':
        from app.translations.en import TRANSLATIONS
    elif lang == 'Portugues':
        from app.translations.pt import TRANSLATIONS
    elif lang == 'Français':
        from app.translations.fr import TRANSLATIONS
    else:
        # Fallback a ingles si el idioma no se reconoce
        from app.translations.en import TRANSLATIONS
    
    return TRANSLATIONS


def t(key, lang=None):
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
