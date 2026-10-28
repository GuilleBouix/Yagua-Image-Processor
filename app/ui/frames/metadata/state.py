"""Catálogo compartido con identidades estables y borradores independientes por imagen."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

from app.modules.metadata_batch import MetadataDraft


def path_key(path: str) -> str:
    """Normaliza una ruta para comparar selecciones en Windows y Linux."""
    return os.path.normcase(str(Path(path).resolve()))


@dataclass
class MetadataItem:
    """Guarda el estado de una imagen dentro del lote EXIF."""
    path: str
    checked: bool = True
    data: dict | None = None
    draft: MetadataDraft = field(default_factory=MetadataDraft)
    status: str = 'meta_pending'
    detail: str = ''
    thumbnail: object = None
    format: str = ''
    size_bytes: int = 0


class MetadataState:
    """Mantiene selección y formularios sin depender de los widgets."""
    limit = 100

    def __init__(self):
        """Inicializa selección, archivo editado y datos visibles."""
        self.items: dict[str, MetadataItem] = {}
        self.active: str | None = None
        self.ruta: str | None = None
        self.ruta_edicion: str | None = None
        self.metadatos: dict[str, str] = {}
        self.last_addition = (0, 0, 0)

    @property
    def imagenes_lote(self) -> list[str]:
        """Devuelve las rutas seleccionadas en orden estable."""
        return [item.path for item in self.items.values()]

    @property
    def current(self) -> MetadataItem | None:
        """Obtiene el elemento actualmente mostrado."""
        return self.items.get(self.active or '')

    @property
    def marked(self) -> list[MetadataItem]:
        """Devuelve los archivos marcados para una operación."""
        return [item for item in self.items.values() if item.checked]

    def add(self, paths: list[str]) -> tuple[list[str], int, int]:
        """Agrega rutas nuevas sin duplicar rutas ya presentes."""
        added, excluded, duplicates = [], 0, 0
        seen = set(self.items)
        for path in paths:
            key = path_key(path)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            if len(self.items) >= self.limit:
                excluded += 1
                continue
            self.items[key] = MetadataItem(str(Path(path).resolve()))
            added.append(key)
        self.last_addition = (len(added), excluded, duplicates)
        return added, excluded, duplicates

    def clear(self):
        """Vacía la selección y los valores transitorios del formulario."""
        self.items.clear()
        self.active = self.ruta = self.ruta_edicion = None
        self.metadatos = {}
        self.last_addition = (0, 0, 0)
