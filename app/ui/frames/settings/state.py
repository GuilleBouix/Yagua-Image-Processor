"""Estado UI para Settings."""

from __future__ import annotations

import customtkinter as ctk
from app.translations import get_language


class SettingsState:
    def __init__(self):
        self.lang_var: ctk.StringVar = ctk.StringVar(value=get_language())
