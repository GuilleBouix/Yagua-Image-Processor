"""
Services UI-agnosticos para el modulo de vectorizacion.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/vectorizar.py: Logica de negocio original.
    - app/ui/frames/vectorizar/frame.py: Usa estas funciones.
"""

from app.modules.vectorizar import batch_vectorizar

__all__ = ["batch_vectorizar"]
