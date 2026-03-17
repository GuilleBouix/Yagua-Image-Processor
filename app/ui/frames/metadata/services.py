"""Services UI-agnosticos para Metadatos."""

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
