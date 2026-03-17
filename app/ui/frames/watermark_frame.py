"""
Frame para agregar marca de agua a imÃ¡genes.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class WatermarkFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        ctk.CTkLabel(
            self,
            text="Watermark â€” proximamente",
            font=fonts.FUENTE_BASE
        ).pack(expand=True)
