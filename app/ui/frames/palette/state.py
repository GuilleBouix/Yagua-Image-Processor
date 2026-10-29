"""Estado de la interfaz para el modulo de Paleta de Colores.

Gestiona las variables de estado de la interfaz grafica:
    - Ruta de la imagen seleccionada
    - Paleta de colores extraida
"""

from __future__ import annotations


class PaletteState:
    """Almacena el estado reactivo de la interfaz de paleta."""

    def __init__(self):
        """Inicializa los datos de imagen y paleta todavía no confirmados."""
        self.ruta: str | None = None
        self.paleta: list[tuple[int, int, int]] = []
        self.paths: list[str] = []

    def add(self, paths):
        """Append unique inputs up to 100; report duplicates and overflow."""
        from app.modules.palette_batch import path_key
        seen = set(self.paths)
        duplicates = excluded = 0
        for path in paths:
            key = path_key(path)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            if len(self.paths) == 100:
                excluded += 1
            else:
                self.paths.append(key)
        return duplicates, excluded
