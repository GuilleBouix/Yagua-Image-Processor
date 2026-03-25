"""
Helpers comunes de preparacion de imagenes.
"""

from __future__ import annotations

from PIL import Image, ImageOps


def normalize_common(imagen: Image.Image) -> Image.Image:
    """
    Normaliza la imagen con operaciones comunes:
    - Corrige orientacion EXIF
    - Convierte CMYK a RGB
    """
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode == 'CMYK':
        imagen = imagen.convert('RGB')
    return imagen


def ensure_rgb_for_jpeg(imagen: Image.Image) -> Image.Image:
    """
    Convierte una imagen a RGB apto para JPEG, manejando transparencia.
    """
    if imagen.mode in ('RGBA', 'LA', 'P'):
        if imagen.mode == 'P':
            imagen = imagen.convert('RGBA')
        fondo = Image.new('RGB', imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.split()[-1] if imagen.mode == 'RGBA' else None)
        return fondo
    return imagen.convert('RGB')
