"""
Services UI-agnosticos para el modulo de compresion.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/compress.py: Logica de negocio original.
    - app/ui/frames/compress/frame.py: Usa estas funciones.
"""

from app.modules.compress import batch_comprimir, estimar_tamano, formatear_bytes


__all__ = [
    'batch_comprimir',
    'estimar_tamano',
    'formatear_bytes',
]
