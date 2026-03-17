"""Estado UI para Metadatos."""

from __future__ import annotations


class MetadataState:
    def __init__(self):
        self.ruta: str | None = None
        self.imagenes_lote: list[str] = []
        self.metadatos: dict[str, str] = {}
