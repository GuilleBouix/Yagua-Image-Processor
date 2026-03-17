"""
Core - LÃ³gica de negocio de la aplicaciÃ³n.
Este mÃ³dulo re-exporta todo desde modules para compatibilidad.
"""

from app.modules.compress import (
    comprimir_imagen,
    estimar_tamano,
    formatear_bytes,
)
from app.modules.convert import (
    convertir_imagen,
    batch_convertir,
    FORMATOS_DESTINO,
)
from app.modules.palette import (
    extraer_paleta,
    exportar_paleta_imagen,
    rgb_a_hex,
    rgb_a_hsl,
    es_color_claro,
    formatos_color,
)
from app.modules.metadata import (
    leer_metadatos,
    limpiar_exif,
    editar_exif,
    exportar_txt,
    exportar_json,
    CAMPOS_EDITABLES,
)
