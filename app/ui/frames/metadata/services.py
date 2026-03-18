"""Servicios UI-agnosticos para lectura, edicion y limpieza de metadatos EXIF.

Proporciona acceso a las funciones de negocio del modulo metadata
sin dependencias de la interfaz grafica.

Relaciones:
    - Logica de negocio: app.modules.metadata
"""

from app.modules.metadata import (
    leer_metadatos_safe,
    editar_exif,
    exportar_metadatos,
    preparar_campos_exif,
    CAMPOS_EDITABLES,
    batch_limpiar_exif,
)

__all__ = [
    'leer_metadatos_safe',
    'editar_exif',
    'exportar_metadatos',
    'preparar_campos_exif',
    'CAMPOS_EDITABLES',
    'batch_limpiar_exif',
]
