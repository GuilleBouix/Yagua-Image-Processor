"""
Frame placeholder para modulos no implementados.
Muestra un mensaje indicando que el modulo aun no esta disponible.

Relacionado con:
    - app/ui/module_registry.py: Registra este frame para modulos deshabilitados.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class PlaceholderFrame(ctk.CTkFrame):
    """
    Frame generico para modulos pendientes de implementacion.
    
    Muestra un label centrado indicando el nombre del modulo
    y que esta funcionalidad viene pronto.
    """
    
    def __init__(self, parent, module_name="Modulo"):
        """
        Inicializa el frame placeholder.
        
        Args:
            parent: Widget padre.
            module_name: Nombre del modulo a mostrar.
        """
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        
        # Mostrar mensaje de modulo proximamente
        ctk.CTkLabel(
            self,
            text=f"{module_name} -- proximamente",
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY
        ).pack(expand=True)
