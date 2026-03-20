"""
Servicios UI-agnosticos para el modulo de renombrado en lote.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/rename.py: Logica de negocio original.
    - app/ui/frames/rename/frame.py: Usa estas funciones.
"""

from app.modules.rename import generar_nombres_preview, renombrar_archivos

__all__ = ['generar_nombres_preview', 'renombrar_archivos']