"""Estado UI para Paleta."""

from __future__ import annotations


class PaletteState:
    def __init__(self):
        self.ruta: str | None = None
        self.paleta: list[tuple[int, int, int]] = []
