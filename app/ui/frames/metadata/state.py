"""Shared collection, stable identities and independent per-image drafts."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

from app.modules.metadata_batch import MetadataDraft


def path_key(path: str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


@dataclass
class MetadataItem:
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
    limit = 100

    def __init__(self):
        self.items: dict[str, MetadataItem] = {}
        self.active: str | None = None
        self.ruta: str | None = None
        self.ruta_edicion: str | None = None
        self.metadatos: dict[str, str] = {}
        self.last_addition = (0, 0, 0)

    @property
    def imagenes_lote(self) -> list[str]:
        return [item.path for item in self.items.values()]

    @property
    def current(self) -> MetadataItem | None:
        return self.items.get(self.active or '')

    @property
    def marked(self) -> list[MetadataItem]:
        return [item for item in self.items.values() if item.checked]

    def add(self, paths: list[str]) -> tuple[list[str], int, int]:
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
        self.items.clear()
        self.active = self.ruta = self.ruta_edicion = None
        self.metadatos = {}
        self.last_addition = (0, 0, 0)
