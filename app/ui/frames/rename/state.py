"""
Estado UI para el modulo de renombrado en lote.

Relacionado con:
    - app/ui/frames/rename/frame.py: Usa este estado.
"""

import customtkinter as ctk


class RenameState:
    """Estado del modulo de renombrado en lote."""

    def __init__(self):
        """Inicializa el estado con valores por defecto."""
        self.imagenes = []

        # Numeracion
        self.numeracion_activa = ctk.BooleanVar(value=False)
        self.prefijo = ctk.StringVar(value='foto')
        self.inicio = ctk.StringVar(value='1')

        # Fecha
        self.fecha_activa = ctk.BooleanVar(value=False)
        self.posicion_fecha = ctk.StringVar(value='prefijo')
        self.formato_fecha = ctk.StringVar(value='%Y%m%d')

        # Capitalización
        self.caso = ctk.StringVar(value='minusculas')

    def obtener_opciones(self):
        """
        Construye el diccionario de opciones para el modulo.

        Returns:
            Diccionario con todas las opciones configuradas.
        """
        try:
            inicio = int(self.inicio.get())
        except (ValueError, TypeError):
            inicio = 1

        return {
            'numeracion_activa': self.numeracion_activa.get(),
            'prefijo':           self.prefijo.get(),
            'inicio':            inicio,
            'fecha_activa':      self.fecha_activa.get(),
            'posicion_fecha':    self.posicion_fecha.get(),
            'formato_fecha':     self.formato_fecha.get(),
            'caso':              self.caso.get(),
        }