"""
Estado UI para el modulo de OCR.
Maneja las variables de estado especificas del modulo.

Relacionado con:
    - app/ui/frames/ocr/frame.py: Usa este estado.
"""

from __future__ import annotations

import customtkinter as ctk


class OcrState:
    """
    Estado del modulo de OCR.
    
    Contiene las variables que representan el estado
    actual de la interfaz del modulo de OCR.
    """
    
    def __init__(self):
        """
        Inicializa el estado con valores por defecto.
        """
        # Lista de rutas de imagenes seleccionadas
        self.imagenes = []
        
        # Texto extraído concatenado
        self.texto_extraido = ctk.StringVar(value='')
        
        # Si está procesando
        self.processing = ctk.BooleanVar(value=False)
        
        # Idiomas seleccionados para OCR
        self.idiomas = ctk.StringVar(value='es,en')
