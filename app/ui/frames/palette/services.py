"""Servicios UI-agnosticos para extraccion de paleta de colores.

Proporciona acceso a las funciones de negocio del modulo palette
sin dependencias de la interfaz grafica.

Relaciones:
    - Logica de negocio: app.modules.palette
"""

from app.modules.palette import (
    cargar_preview,
    extraer_paleta_safe,
    exportar_paleta_imagen,
    formatos_color,
    rgb_a_hex,
)

__all__ = [
    'cargar_preview',
    'extraer_paleta_safe',
    'exportar_paleta_imagen',
    'formatos_color',
    'rgb_a_hex',
]
