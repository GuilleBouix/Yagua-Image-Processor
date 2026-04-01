"""
Servicios UI-agnosticos para el modulo de transformaciones.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/image_transform.py: Logica de negocio original.
    - app/ui/frames/image_transform/frame.py: Usa estas funciones.
"""

from app.modules.image_transform import transformar_imagen, batch_transformar

__all__ = ['transformar_imagen', 'batch_transformar']