"""
Modulo de transformaciones geometricas de imagenes.
Soporta rotacion rapida, libre, volteo y correccion EXIF.

Relacionado con:
    - app/ui/frames/image_transform/: UI relacionada.
"""

import logging
from pathlib import Path

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def transformar_imagen(ruta_entrada, ruta_salida, opciones):
    """
    Aplica transformaciones geometricas a una imagen.

    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar el resultado.
        opciones: Diccionario con las transformaciones a aplicar.

    Returns:
        Diccionario con ruta_salida, ok.
    """
    with Image.open(ruta_entrada) as imagen_in:
        imagen = imagen_in.copy()
        formato_original = imagen_in.format or _formato_desde_ruta(ruta_entrada)

    # Corregir orientacion EXIF antes de cualquier transformacion
    if opciones.get('corregir_exif'):
        imagen = ImageOps.exif_transpose(imagen)
        logger.info(f'Orientacion EXIF corregida: {ruta_entrada}')

    # Rotacion rapida
    rotacion_rapida = opciones.get('rotacion_rapida')
    if rotacion_rapida:
        imagen = _aplicar_rotacion_rapida(imagen, rotacion_rapida)

    # Rotacion libre
    angulo_libre = opciones.get('angulo_libre', 0)
    if angulo_libre != 0:
        color_fondo = _obtener_color_fondo(imagen)
        imagen = imagen.rotate(
            angulo_libre,
            expand=True,
            fillcolor=color_fondo,
            resample=Image.Resampling.BICUBIC
        )

    # Volteos
    if opciones.get('flip_horizontal'):
        imagen = ImageOps.mirror(imagen)
    if opciones.get('flip_vertical'):
        imagen = ImageOps.flip(imagen)

    # Guardar preservando formato y transparencia
    _guardar_imagen(imagen, ruta_salida, formato_original)
    logger.info(f'Transformacion completada: {ruta_salida}')

    return {'ruta_salida': ruta_salida, 'ok': True}


def _aplicar_rotacion_rapida(imagen, rotacion_rapida):
    """Aplica una rotacion rapida segun el valor seleccionado."""
    if rotacion_rapida == '90_izq':
        return imagen.rotate(90, expand=True)
    if rotacion_rapida == '90_der':
        return imagen.rotate(-90, expand=True)
    if rotacion_rapida == '180':
        return imagen.rotate(180, expand=True)
    return imagen


def batch_transformar(rutas, carpeta_salida, opciones):
    """
    Aplica transformaciones a multiples imagenes.

    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar los resultados.
        opciones: Diccionario con las transformaciones a aplicar.

    Returns:
        Diccionario con ok, errores, resultados.
    """
    resultados = []
    errores = 0

    for ruta in rutas:
        try:
            ruta_archivo = Path(ruta)
            ruta_salida = str(
                Path(carpeta_salida) / (ruta_archivo.stem + '_transform' + ruta_archivo.suffix)
            )
            resultado = transformar_imagen(ruta, ruta_salida, opciones)
            resultados.append(resultado)
        except Exception as excepcion:
            logger.warning(f'Error transformando {ruta}: {excepcion}')
            errores += 1

    return {
        'ok':        len(resultados),
        'errores':   errores,
        'resultados': resultados,
    }


def _obtener_color_fondo(imagen):
    """
    Determina el color de relleno segun el modo de la imagen.

    Args:
        imagen: Objeto Image de Pillow.

    Returns:
        Tupla de color o None para transparente.
    """
    if imagen.mode in ('RGBA', 'LA'):
        return (0, 0, 0, 0)
    return (0, 0, 0)


def _guardar_imagen(imagen, ruta_salida, formato):
    """
    Guarda la imagen preservando transparencia y formato.

    Args:
        imagen: Objeto Image procesado.
        ruta_salida: Ruta destino.
        formato: Formato de salida (JPEG, PNG, WEBP, etc.).
    """
    formato = formato.upper()

    # JPEG no soporta transparencia
    if formato in ('JPEG', 'JPG') and imagen.mode in ('RGBA', 'LA', 'P'):
        fondo = Image.new('RGB', imagen.size, (255, 255, 255))
        if imagen.mode == 'P':
            imagen = imagen.convert('RGBA')
        if imagen.mode in ('RGBA', 'LA'):
            fondo.paste(imagen, mask=imagen.split()[-1])
        imagen = fondo

    imagen.save(ruta_salida, formato if formato != 'JPG' else 'JPEG')


def _formato_desde_ruta(ruta):
    """
    Infiere el formato desde la extension del archivo.

    Args:
        ruta: Ruta del archivo.

    Returns:
        String con el formato (ej: 'PNG', 'JPEG').
    """
    extension = Path(ruta).suffix.lower()
    mapa = {
        '.jpg':  'JPEG',
        '.jpeg': 'JPEG',
        '.png':  'PNG',
        '.webp': 'WEBP',
        '.bmp':  'BMP',
        '.tiff': 'TIFF',
        '.gif':  'GIF',
        '.heic': 'HEIF',
        '.heif': 'HEIF',
    }
    return mapa.get(extension, 'PNG')
