"""
Utils - Funciones helper de la aplicaciÃ³n.
"""

import logging
from typing import Optional

import customtkinter as ctk
from PIL import Image


logger = logging.getLogger(__name__)


def tintar_icono(ruta_icono: str, color_hex: str) -> Optional[ctk.CTkImage]:
    try:
        img = Image.open(ruta_icono).convert('RGBA')
    except Exception as exc:
        logger.warning("No se pudo cargar el Ã­cono %s: %s", ruta_icono, exc)
        return None
    
    if color_hex:
        r, g, b = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        r_ch, g_ch, b_ch, a_ch = img.split()
        r_ch = r_ch.point(lambda _: r)
        g_ch = g_ch.point(lambda _: g)
        b_ch = b_ch.point(lambda _: b)
        img = Image.merge('RGBA', (r_ch, g_ch, b_ch, a_ch))

    return ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
