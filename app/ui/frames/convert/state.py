"""
Estado UI para el modulo de conversion.
Maneja las variables de estado especificas del modulo.

Relacionado con:
    - app/ui/frames/convert/frame.py: Usa este estado.
"""

from __future__ import annotations

import customtkinter as ctk


class ConvertState:
    """
    Estado del modulo de conversion.
    
    Contiene las variables que representan el estado
    actual de la interfaz del modulo de conversion.
    """
    
    def __init__(self):
        """
        Inicializa el estado con valores por defecto.
        """
        # Lista de rutas de imagenes seleccionadas
        self.imagenes = []
        
        # Formato de destino para la conversion, default WEBP
        self.fmt_destino = ctk.StringVar(value='WEBP')
        
        # Nivel de calidad (10-100), default 90
        self.calidad = ctk.IntVar(value=90)
