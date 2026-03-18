"""Estado de la interfaz para el modulo de Paleta de Colores.

Gestiona las variables de estado de la interfaz grafica:
    - Ruta de la imagen seleccionada
    - Paleta de colores extraida
"""

from __future__ import annotations


class PaletteState:
    """Almacena el estado reactivo de la interfaz de paleta."""

    def __init__(self):
        self.ruta: str | None = None
        self.paleta: list[tuple[int, int, int]] = []
