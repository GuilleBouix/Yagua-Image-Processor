"""
Frame para generar LQIP (Low Quality Image Placeholders) y Base64.
"""

import customtkinter as ctk

from app.ui import colors, fonts


class LQIPFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        ctk.CTkLabel(
            self,
            text="LQIP â€” proximamente",
            font=fonts.FUENTE_BASE
        ).pack(expand=True)
