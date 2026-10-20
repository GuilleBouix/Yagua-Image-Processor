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
    MetadataEditRequest,
    CAMPOS_EDITABLES,
    GRUPOS_CAMPOS_EDITABLES,
    CAMPOS_VISIBLES,
    GRUPOS_CAMPOS_VISIBLES,
    OPCIONES_ENUM_EXIF,
    ORIENTACIONES_EXIF,
    leer_campos_edicion_safe,
    batch_limpiar_exif,
)
from app.modules.metadata_batch import MetadataDraft, MetadataTask, leer_archivo, procesar_lote, exportar_lote

__all__ = [
    'leer_metadatos_safe',
    'editar_exif',
    'exportar_metadatos',
    'preparar_campos_exif',
    'MetadataEditRequest',
    'CAMPOS_EDITABLES',
    'GRUPOS_CAMPOS_EDITABLES',
    'CAMPOS_VISIBLES',
    'GRUPOS_CAMPOS_VISIBLES',
    'OPCIONES_ENUM_EXIF',
    'ORIENTACIONES_EXIF',
    'leer_campos_edicion_safe',
    'batch_limpiar_exif',
    'MetadataDraft', 'MetadataTask', 'leer_archivo', 'procesar_lote', 'exportar_lote',
]
