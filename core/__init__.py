"""
Core - Lógica de negocio de la aplicación.
Este módulo re-exporta todo desde modules para compatibilidad.
"""

from modules.compress import (
    comprimir_imagen,
    estimar_tamano,
    formatear_bytes,
)
from modules.convert import (
    convertir_imagen,
    batch_convertir,
    FORMATOS_DESTINO,
)
from modules.palette import (
    extraer_paleta,
    exportar_paleta_imagen,
    rgb_a_hex,
    rgb_a_hsl,
    es_color_claro,
    formatos_color,
)
from modules.metadata import (
    leer_metadatos,
    limpiar_exif,
    editar_exif,
    exportar_txt,
    exportar_json,
    CAMPOS_EDITABLES,
)
