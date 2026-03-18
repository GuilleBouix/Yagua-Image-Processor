"""
Estado UI para el modulo de compresion.
Maneja las variables de estado especificas del modulo.

Relacionado con:
    - app/ui/frames/compress/frame.py: Usa este estado.
"""

from __future__ import annotations

import customtkinter as ctk


class CompressState:
    """
    Estado del modulo de compresion.
    
    Contiene las variables que representan el estado
    actual de la interfaz del modulo de compresion.
    """
    
    def __init__(self):
        """
        Inicializa el estado con valores por defecto.
        """
        # Lista de rutas de imagenes seleccionadas
        self.imagenes = []
        
        # Nivel de calidad de compresion (10-100), default 60
        self.calidad = ctk.IntVar(value=60)
        
        # Si es True, elimina metadatos EXIF al comprimir, default True
        self.quitar_exif = ctk.BooleanVar(value=True)
