"""
Estado UI para el modulo de eliminacion de fondo.

Relacionado con:
    - app/ui/frames/remove_bg/frame.py: Usa este estado.
"""

import customtkinter as ctk


class RemoveBgState:
    """
    Estado del modulo de eliminacion de fondo.

    Attributes:
        imagenes: Lista de rutas de imagenes cargadas.
        modo_fondo: 'transparente', 'blanco', 'negro' o 'custom'.
        color_custom: Color personalizado en formato hex.
    """

    def __init__(self):
        """Inicializa el estado con valores por defecto."""
        self.imagenes = []
        self.modo_fondo = ctk.StringVar(value='transparente')
        self.color_custom = ctk.StringVar(value='#FFFFFF')

    def obtener_color_fondo(self):
        """
        Retorna el color de fondo segun el modo seleccionado.

        Returns:
            Tupla (R,G,B) o None para transparente.
        """
        modo = self.modo_fondo.get()

        if modo == 'transparente':
            return None
        elif modo == 'blanco':
            return (255, 255, 255)
        elif modo == 'negro':
            return (0, 0, 0)
        elif modo == 'custom':
            hex_color = self.color_custom.get().lstrip('#')
            try:
                red   = int(hex_color[0:2], 16)
                green = int(hex_color[2:4], 16)
                blue  = int(hex_color[4:6], 16)
                return (red, green, blue)
            except (ValueError, IndexError):
                return (255, 255, 255)

        return None