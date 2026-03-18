"""Estado de la interfaz para el modulo de Metadatos EXIF.

Gestiona las variables de estado de la interfaz grafica:
    - Ruta de la imagen seleccionada
    - Lista de imagenes para procesamiento en lote
    - Diccionario de metadatos cargados
"""

from __future__ import annotations


class MetadataState:
    """Almacena el estado reactivo de la interfaz de metadatos."""

    def __init__(self):
        self.ruta: str | None = None
        self.imagenes_lote: list[str] = []
        self.metadatos: dict[str, str] = {}
