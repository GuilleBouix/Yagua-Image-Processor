"""
Modulo de redimensionado, recorte y canvas de imagenes.
Proporciona funciones para cambiar tamano, recortar y agregar canvas.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/resize/services.py: Usa las funciones de este modulo.
"""

import logging
from pathlib import Path

from PIL import Image
from app.modules.resize_geometry import resize_size, centered_crop, canvas_geometry

from app.utils.image_utils import normalize_common
from app.utils.output import unique_output_path, safe_image_output, DiscardOutput
from app.utils.saving import get_plan, run_plan, canonical_format

from app.utils.results import FileFailure, file_failure

logger = logging.getLogger(__name__)


# Presets de redimensionado por plataforma y uso
PRESETS = {
    'Instagram': {
        'Post cuadrado  1:1':    (1080, 1080),
        'Post portrait  4:5':    (1080, 1350),
        'Story / Reels  9:16':   (1080, 1920),
    },
    'Facebook': {
        'Post  1200x630':        (1200, 630),
        'Cover  851x315':        (851,  315),
    },
    'Twitter / X': {
        'Post  16:9':            (1200, 675),
        'Header  3:1':           (1500, 500),
    },
    'YouTube': {
        'Thumbnail  16:9':       (1280, 720),
        'Channel art  16:9':     (2560, 1440),
    },
    'LinkedIn': {
        'Post  1.91:1':          (1200, 627),
        'Cover personal  4:1':   (1584, 396),
    },
    'TikTok / Whatsapp': {
        'Status / Video  9:16':  (1080, 1920),
    },
    'Pinterest': {
        'Pin estandar  2:3':     (1000, 1500),
    },
    'Web': {
        'OG image  1.91:1':      (1200, 630),
    },
    'Resoluciones': {
        'HD 720p  1280x720':     (1280, 720),
        'Full HD 1080p  1920x1080': (1920, 1080),
        '2K  2560x1440':         (2560, 1440),
        '4K UHD  3840x2160':     (3840, 2160),
    },
    'Iconos': {
        'Favicon  32x32':        (32,   32),
        'Icono 256  256x256':    (256,  256),
        'Icono 512  512x512':    (512,  512),
        'Apple touch  180x180':  (180,  180),
    },
}

# Lista plana de presets para mostrar en dropdown
PRESETS_LISTA = [
    f'{cat} - {nombre}'
    for cat, items in PRESETS.items()
    for nombre in items
]

# Ratios de aspecto disponibles para recorte
RATIOS = {
    '1:1':   (1, 1),
    '4:3':   (4, 3),
    '3:4':   (3, 4),
    '16:9':  (16, 9),
    '9:16':  (9, 16),
    '3:2':   (3, 2),
    '2:3':   (2, 3),
    '21:9':  (21, 9),
}

# Extensiones que soportan transparencia
TRANSPARENCY_EXTS = ('.png', '.webp', '.gif', '.tiff', '.heic', '.heif')


def preset_a_dimensiones(key):
    """
    Convierte una key de preset a dimensiones en pixeles.
    
    Args:
        key: String en formato 'Categoria - Nombre' (ej: 'Instagram - Post cuadrado  1:1').
        
    Returns:
        Tupla (ancho, alto) o None si no se encuentra.
    """
    if ' - ' not in key:
        return None
    cat, nombre = key.split(' - ', 1)
    return PRESETS.get(cat, {}).get(nombre)


@safe_image_output
def redimensionar(ruta_entrada, ruta_salida, ancho=None, alto=None,
                   porcentaje=None, preset_key=None, mantener_ratio=True,
                   resample=Image.Resampling.LANCZOS):
    """
    Redimensiona una imagen a nuevas dimensiones.
    
    Permite especificar tamano por dimensiones exactas, porcentaje
    o preset predefinido.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen redimensionada.
        ancho: Nuevo ancho en pixeles.
        alto: Nuevo alto en pixeles.
        porcentaje: Porcentaje de escala (ej: 50 para reducir a la mitad).
        preset_key: Key de preset predefinido.
        mantener_ratio: Si es True, mantiene la relacion de aspecto.
        resample: Filtro de remuestreo a usar.
        
    Returns:
        Diccionario con dimensiones originales y resultantes.
    """

    logger.info("Redimensionar: %s -> %s", ruta_entrada, ruta_salida)
    with Image.open(ruta_entrada) as imagen:
        formato = imagen.format or _formato_desde_ruta(ruta_entrada)
        imagen = normalize_common(imagen)
        ancho_original, alto_original = imagen.size

        target = resize_size(imagen.size, ancho, alto, porcentaje,
                             preset_a_dimensiones(preset_key) if preset_key else None,
                             mantener_ratio and not preset_key)
        fit = mantener_ratio and not preset_key and porcentaje is None and ancho and alto
        if fit:
            imagen.thumbnail(target, resample)
        else:
            imagen = imagen.resize(target, resample)

        # Guardar en el formato original
        imagen.save(ruta_salida, formato)

        return {
            'ruta_salida': ruta_salida,
            'original': (ancho_original, alto_original),
            'resultado': imagen.size,
        }


@safe_image_output
def recortar(ruta_entrada, ruta_salida, ratio=None,
              izq=0, sup=0, der=None, inf=None, *, ancho=None, alto=None):
    """
    Recorta una imagen segun ratio o coordenadas especificas.
    
    Si se especifica un ratio, el recorte se centra automaticamente.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen recortada.
        ratio: Ratio de aspecto (ej: '16:9', '4:3').
        izq: Coordenada izquierda del recorte.
        sup: Coordenada superior del recorte.
        der: Coordenada derecha del recorte.
        inf: Coordenada inferior del recorte.
        ancho, alto: Tamaño exacto del recorte centrado; deben caber en el original.
        
    Returns:
        Diccionario con dimensiones originales y recortadas.
    """

    logger.info("Recortar: %s -> %s", ruta_entrada, ruta_salida)
    with Image.open(ruta_entrada) as imagen:
        formato = imagen.format or _formato_desde_ruta(ruta_entrada)
        imagen = normalize_common(imagen)
        original_width, original_height = imagen.size

        # Calcular recortes si hay ratio especificado
        if ancho is not None or alto is not None:
            izq, sup, der, inf = centered_crop(imagen.size, dimensions=(ancho, alto))
        elif ratio and ratio in RATIOS:
            izq, sup, der, inf = centered_crop(imagen.size, RATIOS[ratio])
        else:
            # Usar coordenadas proporcionadas o limites de la imagen
            der = der if der is not None else original_width
            inf = inf if inf is not None else original_height

        # Recortar la imagen
        img_recortada = imagen.crop((izq, sup, der, inf))
        
        # Guardar en el formato original
        img_recortada.save(ruta_salida, formato)

        return {
            'ruta_salida': ruta_salida,
            'original': (original_width, original_height),
            'resultado': img_recortada.size,
        }


def canvas_output_format(source_format):
    """Conserva formatos con alfa completo y lienzos libres; usa PNG para los demás."""
    source_format = canonical_format(source_format)
    Image.init()
    return source_format if source_format in {'PNG', 'WEBP', 'TIFF', 'AVIF', 'HEIF'} and source_format in Image.SAVE else 'PNG'


def compose_canvas(image, size, offset, background):
    """Compone alfa una sola vez, compartido por preview y salida real."""
    if any(type(value) is not int or value < 1 for value in size):
        raise ValueError('invalid_dimensions')
    if background is not None and (len(background) != 3 or any(
            type(value) is not int or not 0 <= value <= 255 for value in background)):
        raise ValueError('invalid_option')
    canvas = Image.new('RGBA', size, (*background, 255) if background is not None else (0, 0, 0, 0))
    rgba = image if image.mode == 'RGBA' else image.convert('RGBA')
    canvas.alpha_composite(rgba, dest=offset)
    return canvas


@safe_image_output
def agregar_canvas(ruta_entrada, ruta_salida, ancho_final, alto_final,
                   color_fondo=(255, 255, 255), centrar=True, *, output_format=None):
    """
    Agrega canvas (borde) a una imagen para alcanzar dimensiones especificas.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen con canvas.
        ancho_final: Ancho final deseado.
        alto_final: Alto final deseado.
        color_fondo: Tupla RGB para el color del canvas, o None para transparente.
        centrar: Si es True, centra la imagen en el canvas.
        output_format: Formato explícito del destino; None conserva el original.
        
    Returns:
        Diccionario con dimensiones originales y finales.
    """

    logger.info("Canvas: %s -> %s", ruta_entrada, ruta_salida)
    with Image.open(ruta_entrada) as imagen:
        formato = canonical_format(output_format or imagen.format or _formato_desde_ruta(ruta_entrada))
        imagen = normalize_common(imagen)
        ancho, alto = imagen.size
        original_size = imagen.size

        _, offset = canvas_geometry(imagen.size, (ancho_final, alto_final), centrar)
        # Reducir imagen si es mas grande que el canvas
        if ancho > ancho_final or alto > alto_final:
            imagen.thumbnail((ancho_final, alto_final), Image.Resampling.LANCZOS)
            ancho, alto = imagen.size

        canvas = compose_canvas(imagen, (ancho_final, alto_final), offset, color_fondo)

        # El plan indica el formato; las llamadas directas antiguas conservan el original.
        # JPEG requiere RGB incluso cuando el lienzo de trabajo es RGBA.
        if formato == 'JPEG' and canvas.mode == 'RGBA':
            canvas = canvas.convert('RGB')
        
        # Estos codificadores también cuantizan alfa con su calidad predeterminada.
        # Canvas no ofrece un ajuste de calidad; preservar el canal evita alterar bordes.
        options = {'quality': 100} if color_fondo is None and formato in {'AVIF', 'HEIF'} else {}
        canvas.save(ruta_salida, formato, **options)

        return {
            'ruta_salida': ruta_salida,
            'original': original_size,
            'resultado': (ancho_final, alto_final),
        }


def _formato_desde_ruta(ruta):
    """
    Obtiene el formato PIL desde la extension del archivo.
    
    Args:
        ruta: Ruta del archivo.
        
    Returns:
        Nombre del formato PIL.
    """
    extension = Path(ruta).suffix.lower()
    return {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.webp': 'WEBP',
        '.bmp': 'BMP',
        '.tiff': 'TIFF',
        '.gif': 'GIF',
        '.heic': 'HEIF',
        '.heif': 'HEIF',
    }.get(extension, 'JPEG')


def any_supports_transparency(rutas):
    """
    Verifica si alguna de las imagenes soporta transparencia.
    
    Args:
        rutas: Lista de rutas de archivos.
        
    Returns:
        True si al menos una imagen soporta transparencia.
    """
    return any(Path(r).suffix.lower() in TRANSPARENCY_EXTS for r in rutas)


def canvas_color_for_choice(choice_key, supports_transparency):
    """
    Obtiene el color de canvas segun la opcion seleccionada.
    
    Args:
        choice_key: 'white', 'black' o 'transparent'.
        supports_transparency: Si la imagen soporta transparencia.
        
    Returns:
        Tupla con (color RGB o None, si se uso fallback).
    """
    # Transparente si la opcion es transparent y hay soporte
    if choice_key == 'transparent' and supports_transparency:
        return None, False
    
    # Negro si es transparent pero no hay soporte, o si es black
    if choice_key == 'black' or (choice_key == 'transparent' and not supports_transparency):
        return (0, 0, 0), choice_key == 'transparent'
    
    # Blanco por defecto
    return (255, 255, 255), False


def parse_dimensions(ancho_txt, alto_txt):
    """
    Convierte textos de dimensiones a enteros.
    
    Args:
        ancho_txt: Texto del ancho.
        alto_txt: Texto del alto.
        
    Returns:
        Tupla (ancho, alto, None) o (None, None, 'invalid') si hay error.
    """
    try:
        ancho = int(ancho_txt) if ancho_txt else None
        alto = int(alto_txt) if alto_txt else None
        return ancho, alto, None
    except ValueError:
        return None, None, 'invalid'


def batch_redimensionar(rutas, carpeta_salida, *,
                        porcentaje=None, ancho=None, alto=None,
                        preset_key=None, mantener_ratio=True,
                        sufijo='_redim', output_policy=None):
    """
    Redimensiona multiples imagenes en lote.
    
    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar las imagenes.
        porcentaje: Porcentaje de escala.
        ancho: Ancho destino.
        alto: Alto destino.
        preset_key: Key de preset.
        mantener_ratio: Mantener relacion de aspecto.
        sufijo: Sufijo para el nombre del archivo.
        
    Returns:
        Diccionario con exitos, errores y conflictos.
    """
    if output_policy is not None:
        return run_plan(get_plan(output_policy, rutas, carpeta_salida),
            lambda source, target: redimensionar(source, target, porcentaje=porcentaje,
                ancho=ancho, alto=alto, preset_key=preset_key, mantener_ratio=mantener_ratio))
    fallos: list[FileFailure] = []

    logger.info("Batch redimensionar: %s archivos -> %s", len(rutas), carpeta_salida)
    errores = 0
    conflictos = 0
    
    for ruta in rutas:
        try:
            salida_path, conflicto = unique_output_path(
                carpeta_salida, ruta, sufijo=sufijo
            )
            salida = str(salida_path)
            if conflicto:
                conflictos += 1
            redimensionar(
                ruta, salida,
                porcentaje=porcentaje,
                ancho=ancho,
                alto=alto,
                preset_key=preset_key,
                mantener_ratio=mantener_ratio,
            )
        except Exception as exc:
            fallos.append(file_failure(str(ruta), exc))
            logger.warning("Error al redimensionar %s: %s", ruta, exc)
            errores += 1
    
    return {'fallos': fallos, 'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}


def batch_recortar(rutas, carpeta_salida, *, ratio=None, sufijo='_crop', output_policy=None,
                   ancho=None, alto=None):
    """
    Recorta multiples imagenes en lote.
    
    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar las imagenes.
        ratio: Ratio de recorte.
        sufijo: Sufijo para el nombre del archivo.
        ancho, alto: Tamaño exacto centrado; las entradas pequeñas se omiten.
        
    Returns:
        Diccionario con exitos, errores y conflictos.
    """
    def crop_one(source, target):
        """Omite únicamente el tamaño que no cabe; los demás fallos siguen siendo errores."""
        try:
            return recortar(source, target, ratio=ratio, ancho=ancho, alto=alto)
        except ValueError as error:
            if str(error) == 'crop_too_large':
                raise DiscardOutput(dict(estado='skipped', motivo='crop_too_large')) from error
            raise

    if output_policy is not None:
        return run_plan(get_plan(output_policy, rutas, carpeta_salida),
                        crop_one)
    fallos: list[FileFailure] = []
    omitidas = []

    logger.info("Batch recortar: %s archivos -> %s", len(rutas), carpeta_salida)
    errores = 0
    conflictos = 0
    
    for ruta in rutas:
        try:
            salida_path, conflicto = unique_output_path(
                carpeta_salida, ruta, sufijo=sufijo
            )
            salida = str(salida_path)
            if conflicto:
                conflictos += 1
            crop_one(ruta, salida)
        except DiscardOutput:
            omitidas.append(dict(ruta=str(ruta), motivo='crop_too_large'))
        except Exception as exc:
            fallos.append(file_failure(str(ruta), exc))
            logger.warning("Error al recortar %s: %s", ruta, exc)
            errores += 1
    
    return {'fallos': fallos, 'ok': len(rutas) - errores - len(omitidas), 'errores': errores,
            'conflictos': conflictos, 'omitidos': len(omitidas), 'omitidas': omitidas}


def batch_canvas(rutas, carpeta_salida, *, ancho, alto, color_fondo, sufijo='_canvas', output_policy=None):
    """
    Agrega canvas a multiples imagenes en lote.
    
    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar las imagenes.
        ancho: Ancho final.
        alto: Alto final.
        color_fondo: Color del canvas (RGB o None).
        sufijo: Sufijo para el nombre del archivo.
        
    Returns:
        Diccionario con exitos, errores y conflictos.
    """
    if output_policy is not None:
        resolver = canvas_output_format if color_fondo is None else None
        plan = get_plan(output_policy, rutas, carpeta_salida, format_resolver=resolver)
        formats = {item.source: item.target_format for item in plan.items}
        return run_plan(plan, lambda source, target: agregar_canvas(
            source, target, ancho, alto, color_fondo=color_fondo, output_format=formats[source]))
    fallos: list[FileFailure] = []

    logger.info("Batch canvas: %s archivos -> %s", len(rutas), carpeta_salida)
    errores = 0
    conflictos = 0
    
    for ruta in rutas:
        try:
            with Image.open(ruta) as image:
                original_format = canonical_format(image.format or _formato_desde_ruta(ruta))
            target_format = canvas_output_format(original_format) if color_fondo is None else original_format
            salida_path, conflicto = unique_output_path(
                carpeta_salida, ruta, sufijo=sufijo,
                extension='.png' if target_format != original_format else None,
            )
            salida = str(salida_path)
            if conflicto:
                conflictos += 1
            agregar_canvas(ruta, salida, ancho, alto, color_fondo=color_fondo, output_format=target_format)
        except Exception as exc:
            fallos.append(file_failure(str(ruta), exc))
            logger.warning("Error al aplicar canvas %s: %s", ruta, exc)
            errores += 1
    
    return {'fallos': fallos, 'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}
