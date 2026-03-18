"""
Frame para generar LQIP (Low Quality Image Placeholders) y Base64.
Genera miniaturas de baja calidad para mejorar la percepcion de carga.

Modulo pendiente de implementacion completa.

Relacionado con:
    - app/ui/module_registry.py: Registra este frame.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class LQIPFrame(ctk.CTkFrame):
    """
    Frame para generar LQIP y codigo Base64 de imagenes.
    
    Generara miniaturas de baja calidad y su representacion
    en Base64 para usar como placeholders en desarrollo web.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de LQIP.
        
        Args:
            parent: Widget padre.
        """
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        
        # Mostrar mensaje de modulo proximamente
        ctk.CTkLabel(
            self,
            text="LQIP -- proximamente",
            font=fonts.FUENTE_BASE
        ).pack(expand=True)
