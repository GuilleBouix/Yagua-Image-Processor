"""Servicios UI-agnosticos para redimension, recorte y canvas.

Proporciona acceso a las funciones de negocio del modulo resize
sin dependencias de la interfaz grafica.

Relaciones:
    - Logica de negocio: app.modules.resize
"""

from app.modules.resize import (
    batch_redimensionar,
    batch_recortar,
    batch_canvas,
    PRESETS_LISTA,
    RATIOS,
    any_supports_transparency,
    canvas_color_for_choice,
    parse_dimensions,
)

__all__ = [
    'batch_redimensionar',
    'batch_recortar',
    'batch_canvas',
    'PRESETS_LISTA',
    'RATIOS',
    'any_supports_transparency',
    'canvas_color_for_choice',
    'parse_dimensions',
]
