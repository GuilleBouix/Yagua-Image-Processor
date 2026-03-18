"""
Utils - Funciones helper de la aplicacion.
Contiene utilidades generales usadas en toda la interfaz.

Relacionado con:
    - app/ui/sidebar.py: Usa tintar_icono para cargar iconos de navegacion.
    - app/ui/frames/base.py: Posibles usos futuros para iconos.
"""

import logging
from typing import Optional

import customtkinter as ctk
from PIL import Image


logger = logging.getLogger(__name__)


def tintar_icono(ruta_icono, color_hex):
    """
    Carga un icono y le aplica un tinte de color.
    
    Toma un icono en blanco y negro y lo colorea con el hex
    especificado, retornando un CTkImage listo para usar en
    botones y labels de CustomTkinter.
    
    Args:
        ruta_icono: Ruta al archivo PNG del icono.
        color_hex: Color en formato hexadecimal (ej: '#FFFFFF').
        
    Returns:
        CTkImage con el icono tintado, o None si hay error.
    """
    try:
        # Abrir imagen y convertir a RGBA para manejar transparencia
        img = Image.open(ruta_icono).convert('RGBA')
    except Exception as exc:
        # Registrar warning si no se puede cargar el icono
        logger.warning("No se pudo cargar el icono %s: %s", ruta_icono, exc)
        return None
    
    # Aplicar tinte de color si se especifico
    if color_hex:
        # Extraer componentes RGB del color hex
        r, g, b = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Separar canales de la imagen
        r_ch, g_ch, b_ch, a_ch = img.split()
        
        # Aplicar el color a cada canal
        r_ch = r_ch.point(lambda _: r)
        g_ch = g_ch.point(lambda _: g)
        b_ch = b_ch.point(lambda _: b)
        
        # Unir canales de nuevo
        img = Image.merge('RGBA', (r_ch, g_ch, b_ch, a_ch))
    
    # Crear y retornar CTkImage con tamano de 18x18
    return ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
