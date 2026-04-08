"""
Servicios UI-agnosticos para el modulo de eliminacion de fondo.
Re-exporta las funciones de logica de negocio.

Relacionado con:
    - app/modules/remove_bg.py: Logica de negocio original.
    - app/ui/frames/remove_bg/frame.py: Usa estas funciones.
"""

from app.modules.remove_bg import (
    quitar_fondo,
    batch_quitar_fondo,
    ensure_model,
    estado_rembg,
    rembg_disponible,
    modelo_descargado,
    FORMATOS_SALIDA,
    INSTALL_COMMAND,
)

__all__ = [
    'quitar_fondo',
    'batch_quitar_fondo',
    'ensure_model',
    'estado_rembg',
    'rembg_disponible',
    'modelo_descargado',
    'FORMATOS_SALIDA',
    'INSTALL_COMMAND',
]
