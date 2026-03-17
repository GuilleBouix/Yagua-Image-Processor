"""
Frame placeholder para módulos no implementados.
"""

import customtkinter as ctk
from ui import colors, fonts


class PlaceholderFrame(ctk.CTkFrame):
    def __init__(self, parent, module_name: str = "Módulo"):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        ctk.CTkLabel(
            self,
            text=f"{module_name} — proximamente",
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY
        ).pack(expand=True)
