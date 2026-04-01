"""
Estado UI para el modulo de marca de agua.

Relacionado con:
    - app/ui/frames/watermark/frame.py: Usa este estado.
"""

from __future__ import annotations

import customtkinter as ctk


class WatermarkState:
    """Estado del modulo de marca de agua."""

    def __init__(self):
        self.imagenes = []

        # Ruta de la imagen watermark seleccionada
        self.ruta_watermark = ctk.StringVar(value="")

        # Posición: top-left | top-right | bottom-left | bottom-right | center
        self.posicion = ctk.StringVar(value="bottom-right")

        # Tamaño relativo al ancho de la imagen base (0.05 - 0.80)
        # Se guarda como entero 5-80 y se divide por 100 al usar
        self.escala = ctk.IntVar(value=25)

        # Opacidad 0-100 (se divide por 100 al usar)
        self.opacidad = ctk.IntVar(value=60)

        # Margen en píxeles desde el borde
        self.margen = ctk.IntVar(value=20)

        self.carpeta_salida = ctk.StringVar(value="")