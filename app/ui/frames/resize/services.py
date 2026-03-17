"""Services UI-agnosticos para Resize/Crop/Canvas."""

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
