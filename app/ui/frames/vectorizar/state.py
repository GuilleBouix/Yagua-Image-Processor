"""
Estado UI para el modulo de vectorizacion.

Relacionado con:
    - app/ui/frames/vectorizar/frame.py: Usa este estado.
"""

from __future__ import annotations

import customtkinter as ctk


class VectorizarState:
    """Estado del modulo de vectorizacion."""

    def __init__(self):
        self.imagenes = []

        # Modo de color: 'color' | 'binary'
        self.colormode = ctk.StringVar(value="color")

        # Sliders maestros (0-10, se mapean a params internos en frame.py)
        self.nivel_detalle = ctk.IntVar(value=5)   # → color_precision, layer_difference, length_threshold
        self.limpieza      = ctk.IntVar(value=3)   # → filter_speckle
        self.suavidad      = ctk.IntVar(value=6)   # → corner_threshold, mode
        self.tamano        = ctk.IntVar(value=5)   # → path_precision, max_iterations

        self.carpeta_salida = ctk.StringVar(value="")