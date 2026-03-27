"""Servicios UI-agnosticos para gestion de ajustes de la aplicacion.

Proporciona funciones para persistir y aplicar configuraciones:
    - Cambio de idioma con reinicio de la aplicacion
    - Cambio de tema con reinicio de la aplicacion
    - Lectura y escritura de archivo de configuracion

Relaciones:
    - Traducciones: app.translations
"""

import json
import sys
import subprocess
from pathlib import Path

from app.translations import set_language
from app.utils.settings import settings_path


def _settings_path() -> Path:
    """Obtener ruta del archivo de configuracion de usuario."""
    return settings_path()


def _load_settings() -> dict:
    """Cargar configuracion desde el archivo JSON.

    Returns:
        Diccionario con la configuracion guardada o vacio si no existe
    """
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save_settings(settings: dict) -> None:
    """Guardar configuracion en el archivo JSON.

    Args:
        settings: Diccionario con la configuracion a guardar
    """
    path = _settings_path()
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


def get_visible_modules() -> list[str] | None:
    """Retornar la lista de modulos visibles guardada."""
    settings = _load_settings()
    visible = settings.get('visible_modules')
    if not isinstance(visible, list):
        return None
    return [str(v) for v in visible]


def set_visible_modules_and_restart(modules: list[str]) -> None:
    """Guardar modulos visibles y reiniciar la aplicacion."""
    settings = _load_settings()
    settings['visible_modules'] = modules
    _save_settings(settings)
    restart_app()


def restart_app() -> None:
    """Reiniciar la aplicacion con los mismos argumentos."""
    python = sys.executable
    script = sys.argv[0]
    subprocess.Popen([python, script])
    sys.exit(0)


def set_language_and_restart(lang: str) -> None:
    """Cambiar idioma y reiniciar la aplicacion.

    Args:
        lang: Codigo de idioma a establecer
    """
    set_language(lang)
    restart_app()


def set_theme_and_restart(theme: str) -> None:
    """Cambiar tema y reiniciar la aplicacion.

    Args:
        theme: Nombre del tema a establecer
    """
    settings = _load_settings()
    settings['theme'] = theme
    _save_settings(settings)
    restart_app()


__all__ = [
    'set_language_and_restart',
    'set_theme_and_restart',
    'get_visible_modules',
    'set_visible_modules_and_restart',
    'restart_app'
]
