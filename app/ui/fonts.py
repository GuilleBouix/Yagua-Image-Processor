"""
DefiniciÃ³n de fuentes personalizadas para la aplicación.
Carga la fuente Inter y define variables globales reutilizables.
"""

import os
import tkinter.font as tkfont

import customtkinter as ctk


def cargar_fuente(ruta_fuente: str) -> tkfont.Font:
    """
    Carga una fuente desde un archivo TTF.
    
    Args:
        ruta_fuente: Ruta absoluta al archivo .ttf
        
    Returns:
        Objeto Font cargado
    """
    ruta_absoluta = os.path.abspath(ruta_fuente)
    return tkfont.Font(family=os.path.splitext(os.path.basename(ruta_absoluta))[0])


RUTA_FUENTE_INTER = 'assets/fonts/Inter.ttf'

FUENTE_BASE = None
FUENTE_TITULO = None
FUENTE_CHICA = None

def inicializar_fuentes():
    """Inicializa las fuentes personalizadas del proyecto."""
    global FUENTE_BASE, FUENTE_TITULO, FUENTE_CHICA
    
    fuente = cargar_fuente(RUTA_FUENTE_INTER)
    nombre_fuente = fuente.actual()['family']  # type: ignore[return-value]
    
    FUENTE_BASE = ctk.CTkFont(family=nombre_fuente, size=14)  # type: ignore[arg-type]
    FUENTE_TITULO = ctk.CTkFont(family=nombre_fuente, size=22, weight='bold')  # type: ignore[arg-type]
    FUENTE_CHICA = ctk.CTkFont(family=nombre_fuente, size=12)  # type: ignore[arg-type]
