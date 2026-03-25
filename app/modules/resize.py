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

from app.modules.image_utils import normalize_common
from app.modules.output import unique_output_path

from math import gcd

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
TRANSPARENCY_EXTS = ('.png', '.webp', '.gif', '.tiff')


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
    with Image.open(ruta_entrada) as imagen:
        imagen = normalize_common(imagen)
        ancho_original, alto_original = imagen.size

        # Si hay preset, usar sus dimensiones
        if preset_key:
            dims = preset_a_dimensiones(preset_key)
            if dims:
                ancho, alto = dims
            mantener_ratio = False

        # Si hay porcentaje, calcular dimensiones relativas
        elif porcentaje is not None:
            ancho = max(1, int(ancho_original * porcentaje / 100))
            alto = max(1, int(alto_original * porcentaje / 100))
            mantener_ratio = False

        # Si solo se especifica ancho, calcular alto proporcional
        elif ancho and not alto:
            alto = max(1, int(alto_original * ancho / ancho_original))
            mantener_ratio = False

        # Si solo se especifica alto, calcular ancho proporcional
        elif alto and not ancho:
            ancho = max(1, int(ancho_original * alto / alto_original))
            mantener_ratio = False

        # Validar que haya dimensiones
        if not ancho or not alto:
            raise ValueError('Especifica dimensiones, porcentaje o preset.')

        # Redimensionar manteniendo o no la relacion de aspecto
        if mantener_ratio:
            imagen.thumbnail((ancho, alto), resample)
        else:
            imagen = imagen.resize((ancho, alto), resample)

        # Guardar en el formato original
        formato = _formato_desde_ruta(ruta_entrada)
        imagen.save(ruta_salida, formato)

        return {
            'ruta_salida': ruta_salida,
            'original': (ancho_original, alto_original),
            'resultado': imagen.size,
        }


def recortar(ruta_entrada, ruta_salida, ratio=None,
              izq=0, sup=0, der=None, inf=None):
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
        
    Returns:
        Diccionario con dimensiones originales y recortadas.
    """
    with Image.open(ruta_entrada) as imagen:
        imagen = normalize_common(imagen)
        ancho, alto = imagen.size

        # Calcular recortes si hay ratio especificado
        if ratio and ratio in RATIOS:
            rx, ry = RATIOS[ratio]
            
            # Determinar tamano del recorte manteniendo el ratio
            if ancho / alto > rx / ry:
                nuevo_ancho = int(alto * rx / ry)
                nuevo_alto = alto
            else:
                nuevo_ancho = ancho
                nuevo_alto = int(ancho * ry / rx)
            
            # Centrar el recorte
            izq = (ancho - nuevo_ancho) // 2
            sup = (alto - nuevo_alto) // 2
            der = izq + nuevo_ancho
            inf = sup + nuevo_alto
        else:
            # Usar coordenadas proporcionadas o limites de la imagen
            der = der if der is not None else ancho
            inf = inf if inf is not None else alto

        # Recortar la imagen
        img_recortada = imagen.crop((izq, sup, der, inf))
        
        # Guardar en el formato original
        formato = _formato_desde_ruta(ruta_entrada)
        img_recortada.save(ruta_salida, formato)

        return {
            'ruta_salida': ruta_salida,
            'original': (ancho, alto),
            'resultado': img_recortada.size,
        }


def agregar_canvas(ruta_entrada, ruta_salida, ancho_final, alto_final,
                   color_fondo=(255, 255, 255), centrar=True):
    """
    Agrega canvas (borde) a una imagen para alcanzar dimensiones especificas.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen con canvas.
        ancho_final: Ancho final deseado.
        alto_final: Alto final deseado.
        color_fondo: Tupla RGB para el color del canvas, o None para transparente.
        centrar: Si es True, centra la imagen en el canvas.
        
    Returns:
        Diccionario con dimensiones originales y finales.
    """
    with Image.open(ruta_entrada) as imagen:
        imagen = normalize_common(imagen)
        ancho, alto = imagen.size

        # Reducir imagen si es mas grande que el canvas
        if ancho > ancho_final or alto > alto_final:
            imagen.thumbnail((ancho_final, alto_final), Image.Resampling.LANCZOS)
            ancho, alto = imagen.size

        # Crear canvas con el tamano final
        if color_fondo is None:
            # Canvas transparente
            canvas = Image.new('RGBA', (ancho_final, alto_final), (0, 0, 0, 0))
            if imagen.mode != 'RGBA':
                imagen = imagen.convert('RGBA')
        else:
            # Canvas con color solido
            modo = 'RGBA' if imagen.mode == 'RGBA' else 'RGB'
            fondo_color = (*color_fondo, 255) if modo == 'RGBA' else color_fondo
            canvas = Image.new(modo, (ancho_final, alto_final), fondo_color)

        # Calcular posicion para centrar o esquina superior
        coord_x = (ancho_final - ancho) // 2 if centrar else 0
        coord_y = (alto_final - alto) // 2 if centrar else 0

        # Pegar la imagen en el canvas
        if imagen.mode == 'RGBA':
            canvas.paste(imagen, (coord_x, coord_y), mask=imagen.split()[3])
        else:
            canvas.paste(imagen, (coord_x, coord_y))

        # Guardar en el formato original
        formato = _formato_desde_ruta(ruta_entrada)
        
        # Convertir a RGB si es JPEG y tiene transparencia
        if formato == 'JPEG' and canvas.mode == 'RGBA':
            canvas = canvas.convert('RGB')
        
        canvas.save(ruta_salida, formato)

        return {
            'ruta_salida': ruta_salida,
            'original': (ancho, alto),
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
                        sufijo='_redim'):
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
            logger.warning("Error al redimensionar %s: %s", ruta, exc)
            errores += 1
    
    return {'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}


def batch_recortar(rutas, carpeta_salida, *, ratio=None, sufijo='_crop'):
    """
    Recorta multiples imagenes en lote.
    
    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar las imagenes.
        ratio: Ratio de recorte.
        sufijo: Sufijo para el nombre del archivo.
        
    Returns:
        Diccionario con exitos, errores y conflictos.
    """
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
            recortar(ruta, salida, ratio=ratio)
        except Exception as exc:
            logger.warning("Error al recortar %s: %s", ruta, exc)
            errores += 1
    
    return {'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}


def batch_canvas(rutas, carpeta_salida, *, ancho, alto, color_fondo, sufijo='_canvas'):
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
            agregar_canvas(ruta, salida, ancho, alto, color_fondo=color_fondo)
        except Exception as exc:
            logger.warning("Error al aplicar canvas %s: %s", ruta, exc)
            errores += 1
    
    return {'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}
