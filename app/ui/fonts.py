"""
Definicion de fuentes personalizadas para la aplicacion.
Carga la fuente Inter y define variables globales reutilizables.

Relacionado con:
    - app/app.py: Llama a inicializar_fuentes() al iniciar.
    - app/ui/sidebar.py: Usa las fuentes para labels y botones.
    - app/ui/frames/base.py: Usa las fuentes para elementos de UI.
"""

import os
import tkinter.font as tkfont

import customtkinter as ctk


def cargar_fuente(ruta_fuente):
    """
    Carga una fuente desde un archivo TTF.
    
    Args:
        ruta_fuente: Ruta al archivo .ttf de la fuente.
        
    Returns:
        Objeto Font listo para usar con Tkinter.
    """
    # Convertir a ruta absoluta
    ruta_absoluta = os.path.abspath(ruta_fuente)
    
    # Extraer nombre de la fuente del nombre del archivo
    nombre = os.path.splitext(os.path.basename(ruta_absoluta))[0]
    
    # Cargar y retornar la fuente
    return tkfont.Font(family=nombre)


# Ruta a la fuente Inter
RUTA_FUENTE_INTER = 'assets/fonts/Inter.ttf'

# Variables globales para fuentes (se inicializan en inicializar_fuentes)
FUENTE_BASE = None
FUENTE_TITULO = None
FUENTE_CHICA = None


def inicializar_fuentes():
    """
    Inicializa las fuentes personalizadas del proyecto.
    
    Carga la fuente Inter desde assets y crea tres variantes:
    base (14px), titulo (22px bold) y chica (12px).
    """
    global FUENTE_BASE, FUENTE_TITULO, FUENTE_CHICA
    
    # Cargar fuente Inter
    fuente = cargar_fuente(RUTA_FUENTE_INTER)
    
    # Obtener nombre de la fuente cargada
    nombre_fuente = fuente.actual()['family']
    
    # Crear variantes de la fuente
    FUENTE_BASE = ctk.CTkFont(family=nombre_fuente, size=14)
    FUENTE_TITULO = ctk.CTkFont(family=nombre_fuente, size=22, weight='bold')
    FUENTE_CHICA = ctk.CTkFont(family=nombre_fuente, size=12)
