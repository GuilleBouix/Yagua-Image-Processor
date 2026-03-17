"""Estado UI para Convertir."""

from __future__ import annotations

import customtkinter as ctk


class ConvertState:
    def __init__(self):
        self.imagenes: list[str] = []
        self.fmt_destino: ctk.StringVar = ctk.StringVar(value='WEBP')
        self.calidad: ctk.IntVar = ctk.IntVar(value=90)
