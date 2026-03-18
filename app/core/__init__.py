"""
Core - Logica de negocio de la aplicacion.
Este modulo re-exporta funciones desde modules para compatibilidad.

Provee un punto de acceso centralizado a las funciones de procesamiento
de imagenes, evitando que el codigo dependa directamente de modules/.

Relacionado con:
    - app/modules/compress.py: Compression de imagenes.
    - app/modules/convert.py: Conversion de formatos.
    - app/modules/palette.py: Extraccion de paleta de colores.
    - app/modules/metadata.py: Gestion de metadatos EXIF.
"""

# Re-exportar funciones de compresion
from app.modules.compress import (
    comprimir_imagen,
    estimar_tamano,
    formatear_bytes,
)

# Re-exportar funciones de conversion
from app.modules.convert import (
    convertir_imagen,
    batch_convertir,
    FORMATOS_DESTINO,
)

# Re-exportar funciones de paleta de colores
from app.modules.palette import (
    extraer_paleta,
    exportar_paleta_imagen,
    rgb_a_hex,
    rgb_a_hsl,
    es_color_claro,
    formatos_color,
)

# Re-exportar funciones de metadatos EXIF
from app.modules.metadata import (
    leer_metadatos,
    limpiar_exif,
    editar_exif,
    exportar_txt,
    exportar_json,
    CAMPOS_EDITABLES,
)
