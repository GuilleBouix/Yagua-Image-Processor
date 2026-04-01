"""
Helper para obtener la ruta del archivo de configuracion de usuario.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def settings_path() -> Path:
    """Retorna la ruta a user_settings.json en AppData."""
    appdata = os.getenv('APPDATA')
    if sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(appdata) if appdata else (Path.home() / '.config')
    carpeta = base / 'Yagua'
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / 'user_settings.json'


__all__ = ['settings_path']
