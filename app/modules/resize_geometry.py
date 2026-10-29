"""Cálculos compartidos entre guardado y previews de Redimensionar.

No reserva píxeles: opera sobre dimensiones originales ya orientadas.
Relacionado con app.modules.resize y app.ui.preview.
"""
from math import ceil, floor


def fit_size(size, bounds):
    """Reproduce el redondeo de Pillow.thumbnail sin ampliar ni reservar píxeles."""
    width, height = size
    x, y = map(floor, bounds)
    if x >= width and y >= height:
        return size
    aspect = width / height
    if x / y >= aspect:
        number = y * aspect
        x = max(min(floor(number), ceil(number), key=lambda n: abs(aspect - n / y)), 1)
    else:
        number = x / aspect
        y = max(min(floor(number), ceil(number), key=lambda n: 0 if n == 0 else abs(aspect - x / n)), 1)
    return x, y


def resize_size(size, ancho=None, alto=None, porcentaje=None, preset=None, mantener_ratio=True):
    """Resuelve porcentaje, preset o píxeles conservando las reglas del guardado."""
    width, height = size
    if preset:
        ancho, alto = preset
        mantener_ratio = False
    elif porcentaje is not None:
        ancho, alto = max(1, int(width * porcentaje / 100)), max(1, int(height * porcentaje / 100))
        mantener_ratio = False
    elif ancho and not alto:
        alto = max(1, int(height * ancho / width))
        mantener_ratio = False
    elif alto and not ancho:
        ancho = max(1, int(width * alto / height))
        mantener_ratio = False
    if not ancho or not alto or ancho < 1 or alto < 1:
        raise ValueError('invalid_dimensions')
    return fit_size(size, (ancho, alto)) if mantener_ratio else (ancho, alto)


def centered_crop(size, ratio):
    """Calcula el recorte centrado en coordenadas enteras del original."""
    width, height = size
    rx, ry = ratio
    crop_width, crop_height = ((int(height * rx / ry), height) if width / height > rx / ry
                               else (width, int(width * ry / rx)))
    left, top = (width - crop_width) // 2, (height - crop_height) // 2
    return left, top, left + crop_width, top + crop_height


def canvas_geometry(size, bounds, center=True):
    """Calcula tamaño y posición de la imagen contenida en el lienzo final."""
    fitted = fit_size(size, bounds)
    offset = tuple((bound - value) // 2 for bound, value in zip(bounds, fitted)) if center else (0, 0)
    return fitted, offset
