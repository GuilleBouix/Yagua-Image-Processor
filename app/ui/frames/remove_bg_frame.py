"""
Frame para quitar el fondo de imagenes.
Usa IA para eliminar el fondo de forma automatica.

Modulo pendiente de implementacion completa.

Relacionado con:
    - app/ui/module_registry.py: Registra este frame.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class RemoveBgFrame(ctk.CTkFrame):
    """
    Frame para eliminar el fondo de imagenes.
    
    Utilizara la biblioteca rembg para detectar y
    eliminar el fondo usando inteligencia artificial.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de quitar fondo.
        
        Args:
            parent: Widget padre.
        """
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        
        # Mostrar mensaje de modulo proximamente
        ctk.CTkLabel(
            self,
            text="Remove Background -- proximamente",
            font=fonts.FUENTE_BASE
        ).pack(expand=True)
