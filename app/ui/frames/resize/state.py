"""Estado de la interfaz para el modulo de Redimensionar, Recortar y Canvas.

Gestiona las variables de estado de la interfaz grafica:
    - Modo de redimension (porcentaje, pixeles o preset)
    - Configuracion de aspecto y proporciones
    - Color de fondo para canvas
    - Lista de imagenes seleccionadas
"""

from __future__ import annotations

import customtkinter as ctk
from app.translations import t
from app.modules.resize import PRESETS_LISTA


class ResizeState:
    """Almacena el estado reactivo de la interfaz de redimension."""

    def __init__(self):
        """Inicializa los valores de redimensionado, recorte y lienzo."""
        self.imagenes: list[str] = []
        self.width_var = ctk.StringVar(value='')
        self.height_var = ctk.StringVar(value='')
        self.canvas_width_var = ctk.StringVar(value='1080')
        self.canvas_height_var = ctk.StringVar(value='1080')
        self.modo_resize: ctk.StringVar = ctk.StringVar(value=t('percentage'))
        self.mantener_ratio: ctk.BooleanVar = ctk.BooleanVar(value=True)
        self.pct_var: ctk.IntVar = ctk.IntVar(value=50)
        self.ratio_var: ctk.StringVar = ctk.StringVar(value='1:1')
        self.crop_mode = ctk.StringVar(value=t('crop_mode_ratio'))
        self.crop_width_var = ctk.StringVar(value='')
        self.crop_height_var = ctk.StringVar(value='')
        self.color_fondo: ctk.StringVar = ctk.StringVar(value=t('canvas_color'))
        self.canvas_color = ctk.StringVar(value='#FFFFFF')
        self.preset_var: ctk.StringVar = ctk.StringVar(value=PRESETS_LISTA[0])
