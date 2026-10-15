"""
Helper para obtener la ruta del archivo de configuracion de usuario.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def settings_path() -> Path:
    """Retorna la ruta a user_settings.json segun la plataforma."""
    if sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    elif sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        base = Path(appdata) if appdata else (Path.home() / 'AppData' / 'Roaming')
    else:
        base = Path.home() / '.config'
    carpeta = base / 'Yagua'
    return carpeta / 'user_settings.json'


__all__ = ['settings_path']


def load_settings(path: Path | None = None) -> dict:
    """Invalid or inaccessible preferences must not prevent startup."""
    try:
        data = json.loads((path or settings_path()).read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return {}
        validators = {
            'language': lambda v: isinstance(v, str) and v in ('Español', 'English', 'Portugues', 'Français', 'Deutsch'),
            'theme': lambda v: isinstance(v, str),
            'ui_scale': lambda v: type(v) is int and v in (50, 75, 100),
            'visible_modules': lambda v: isinstance(v, list) and all(isinstance(item, str) for item in v),
        }
        return {key: value for key, value in data.items() if key not in validators or validators[key](value)}
    except (OSError, ValueError, TypeError):
        return {}


def save_settings(data: dict, path: Path | None = None) -> None:
    from app.utils.output import atomic_write_text
    if not isinstance(data, dict):
        raise ValueError('Preferences must be an object')
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(target, json.dumps(data, ensure_ascii=False, indent=2))
