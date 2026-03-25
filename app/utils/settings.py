"""
Helper para obtener la ruta del archivo de configuracion de usuario.
"""

from __future__ import annotations

from pathlib import Path


def settings_path() -> Path:
    """Retorna la ruta a user_settings.json en el directorio app/."""
    return Path(__file__).resolve().parents[1] / 'user_settings.json'


__all__ = ['settings_path']
