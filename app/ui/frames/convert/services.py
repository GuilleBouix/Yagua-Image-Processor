"""
Services UI-agnosticos para el modulo de conversion.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/convert.py: Logica de negocio original.
    - app/ui/frames/convert/frame.py: Usa estas funciones.
"""

from app.modules.convert import (
    batch_convertir_safe,
    FORMATOS_DESTINO,
    formato_soporta_calidad,
)


__all__ = [
    'batch_convertir_safe',
    'FORMATOS_DESTINO',
    'formato_soporta_calidad',
]
