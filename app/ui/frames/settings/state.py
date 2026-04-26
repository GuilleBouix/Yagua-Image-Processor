"""Estado de la interfaz para el modulo de Ajustes.

Gestiona las variables de estado de la interfaz grafica:
    - Idioma seleccionado
    - Tema de interfaz seleccionado
"""

from __future__ import annotations

import customtkinter as ctk
from app.translations import get_language
from app.ui import colors
from app.ui.frames.settings.services import get_ui_scale


class SettingsState:
    """Almacena el estado reactivo de la interfaz de ajustes."""

    def __init__(self):
        self.lang_var: ctk.StringVar = ctk.StringVar(value=get_language())
        self.theme_var: ctk.StringVar = ctk.StringVar(value=colors.get_current_theme())
        self.scale_var: ctk.StringVar = ctk.StringVar(value=f'{get_ui_scale()}%')
