"""Estado UI para Comprimir."""

from __future__ import annotations

import customtkinter as ctk


class CompressState:
    def __init__(self):
        self.imagenes: list[str] = []
        self.calidad: ctk.IntVar = ctk.IntVar(value=60)
        self.quitar_exif: ctk.BooleanVar = ctk.BooleanVar(value=True)
