"""
Helpers para gestionar el escalado global de la interfaz.
"""

from __future__ import annotations

import json

import customtkinter as ctk

from app.utils.settings import settings_path

DEFAULT_UI_SCALE = 100
VALID_UI_SCALES = {100, 75, 50}


def _load_settings() -> dict:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_ui_scale_percent() -> int:
    """Retorna el porcentaje de escala configurado para la interfaz."""
    value = _load_settings().get('ui_scale', DEFAULT_UI_SCALE)
    try:
        scale = int(value)
    except (TypeError, ValueError):
        return DEFAULT_UI_SCALE
    return scale if scale in VALID_UI_SCALES else DEFAULT_UI_SCALE


def get_ui_scale_factor() -> float:
    """Retorna el factor flotante para CustomTkinter."""
    return get_ui_scale_percent() / 100.0


def apply_ui_scale() -> None:
    """Aplica el escalado global a widgets y ventanas."""
    factor = get_ui_scale_factor()
    ctk.set_widget_scaling(factor)
    ctk.set_window_scaling(factor)


def scale_wraplength(px: int) -> int:
    """Escala valores de wraplength que no son gestionados automaticamente."""
    return max(1, round(px * get_ui_scale_factor()))


__all__ = [
    'DEFAULT_UI_SCALE',
    'VALID_UI_SCALES',
    'get_ui_scale_percent',
    'get_ui_scale_factor',
    'apply_ui_scale',
    'scale_wraplength',
]
