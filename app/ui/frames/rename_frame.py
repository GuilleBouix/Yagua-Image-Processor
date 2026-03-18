"""
Frame para renombrar imagenes en lote.
Permite renombrar multiples archivos con patrones personalizables.

Modulo pendiente de implementacion completa.

Relacionado con:
    - app/ui/module_registry.py: Registra este frame.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class RenameFrame(ctk.CTkFrame):
    """
    Frame para renombrar archivos de imagen en lote.
    
    Permitira renombrar multiples archivos usando prefijos,
    sufijos, reemplazos de texto y numeracion.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de renombrar.
        
        Args:
            parent: Widget padre.
        """
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        
        # Mostrar mensaje de modulo proximamente
        ctk.CTkLabel(
            self,
            text="Rename -- proximamente",
            font=fonts.FUENTE_BASE
        ).pack(expand=True)
