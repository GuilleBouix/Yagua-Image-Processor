"""
Services UI-agnosticos para el modulo de marca de agua.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/watermark.py: Logica de negocio original.
    - app/ui/frames/watermark/frame.py: Usa estas funciones.
"""

from app.modules.watermark import (
    aplicar_watermark,
    aplicar_watermark_np,
    batch_aplicar_watermark,
)

__all__ = ["aplicar_watermark", "aplicar_watermark_np", "batch_aplicar_watermark"]