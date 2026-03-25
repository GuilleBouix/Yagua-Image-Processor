"""
Estado UI para el modulo LQIP / Base64.

Relacionado con:
    - app/ui/frames/lqip/frame.py: Usa este estado.
"""

import customtkinter as ctk


class LqipState:
    """Estado del modulo LQIP / Base64."""

    def __init__(self):
        """Inicializa el estado con valores por defecto."""
        self.imagenes = []
        self.resultados = []

        # Modo de procesamiento (valores internos, no traducidos)
        self.modo = ctk.StringVar(value='lqip')

        # Opciones LQIP
        self.ancho_lqip = ctk.StringVar(value='20')
        self.blur = ctk.StringVar(value='2')
        self.calidad_lqip = ctk.IntVar(value=40)

        # Opciones base64 completo
        self.calidad_b64 = ctk.IntVar(value=85)

    def obtener_opciones(self):
        """
        Construye el diccionario de opciones.

        Returns:
            Diccionario con todas las opciones configuradas.
        """
        try:
            ancho = int(self.ancho_lqip.get())
        except (ValueError, TypeError):
            ancho = 20

        try:
            blur = float(self.blur.get())
        except (ValueError, TypeError):
            blur = 2.0

        return {
            'modo':          self.modo.get(),
            'ancho':         ancho,
            'blur':          blur,
            'calidad_lqip':  self.calidad_lqip.get(),
            'calidad_b64':   self.calidad_b64.get(),
        }