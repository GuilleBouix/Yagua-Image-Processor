"""
MÃ³dulo de redimensionado, recorte y canvas de imÃ¡genes.
"""

from pathlib import Path
from PIL import Image, ImageOps
from math import gcd


PRESETS: dict[str, dict[str, tuple[int, int]]] = {
    'Instagram': {
        'Post cuadrado  1:1':    (1080, 1080),
        'Post portrait  4:5':    (1080, 1350),
        'Story / Reels  9:16':   (1080, 1920),
    },
    'Facebook': {
        'Post  1200Ã—630':        (1200, 630),
        'Cover  851Ã—315':        (851,  315),
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
        'Pin estÃ¡ndar  2:3':     (1000, 1500),
    },
    'Web': {
        'OG image  1.91:1':      (1200, 630),
    },
    'Resoluciones': {
        'HD 720p  1280Ã—720':     (1280, 720),
        'Full HD 1080p  1920Ã—1080': (1920, 1080),
        '2K  2560Ã—1440':         (2560, 1440),
        '4K UHD  3840Ã—2160':     (3840, 2160),
    },
    'Ãconos': {
        'Favicon  32Ã—32':        (32,   32),
        'Ãcono 256  256Ã—256':    (256,  256),
        'Ãcono 512  512Ã—512':    (512,  512),
        'Apple touch  180Ã—180':  (180,  180),
    },
}

PRESETS_LISTA: list[str] = [
    f'{cat} Â· {nombre}'
    for cat, items in PRESETS.items()
    for nombre in items
]

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

TRANSPARENCY_EXTS = ('.png', '.webp', '.gif', '.tiff')


def preset_a_dimensiones(key: str) -> tuple[int, int] | None:
    """Convierte 'CategorÃ­a Â· Nombre' a (ancho, alto)."""
    if ' Â· ' not in key:
        return None
    cat, nombre = key.split(' Â· ', 1)
    return PRESETS.get(cat, {}).get(nombre)


def redimensionar(
    ruta_entrada: str,
    ruta_salida: str,
    ancho: int | None = None,
    alto: int | None = None,
    porcentaje: float | None = None,
    preset_key: str | None = None,
    mantener_ratio: bool = True,
    resample: int = Image.Resampling.LANCZOS
) -> dict:
    with Image.open(ruta_entrada) as img:
        img = ImageOps.exif_transpose(img)
        w_orig, h_orig = img.size

        if preset_key:
            dims = preset_a_dimensiones(preset_key)
            if dims:
                ancho, alto = dims
            mantener_ratio = False

        elif porcentaje is not None:
            ancho = max(1, int(w_orig * porcentaje / 100))
            alto = max(1, int(h_orig * porcentaje / 100))
            mantener_ratio = False

        elif ancho and not alto:
            alto = max(1, int(h_orig * ancho / w_orig))
            mantener_ratio = False

        elif alto and not ancho:
            ancho = max(1, int(w_orig * alto / h_orig))
            mantener_ratio = False

        if not ancho or not alto:
            raise ValueError('EspecificÃ¡ dimensiones, porcentaje o preset.')

        if mantener_ratio:
            img.thumbnail((ancho, alto), resample) # type: ignore
        else:
            img = img.resize((ancho, alto), resample)

        fmt = _formato_desde_ruta(ruta_entrada)
        img.save(ruta_salida, fmt)

        return {
            'ruta_salida': ruta_salida,
            'original': (w_orig, h_orig),
            'resultado': img.size,
        }


def recortar(
    ruta_entrada: str,
    ruta_salida: str,
    ratio: str | None = None,
    izq: int = 0, sup: int = 0,
    der: int | None = None, inf: int | None = None,
) -> dict:
    with Image.open(ruta_entrada) as img:
        img = ImageOps.exif_transpose(img)
        w, h = img.size

        if ratio and ratio in RATIOS:
            rx, ry = RATIOS[ratio]
            if w / h > rx / ry:
                nuevo_w = int(h * rx / ry)
                nuevo_h = h
            else:
                nuevo_w = w
                nuevo_h = int(w * ry / rx)
            izq = (w - nuevo_w) // 2
            sup = (h - nuevo_h) // 2
            der = izq + nuevo_w
            inf = sup + nuevo_h
        else:
            der = der if der is not None else w
            inf = inf if inf is not None else h

        img_recortada = img.crop((izq, sup, der, inf))
        fmt = _formato_desde_ruta(ruta_entrada)
        img_recortada.save(ruta_salida, fmt)

        return {
            'ruta_salida': ruta_salida,
            'original': (w, h),
            'resultado': img_recortada.size,
        }


def agregar_canvas(
    ruta_entrada: str,
    ruta_salida: str,
    ancho_final: int,
    alto_final: int,
    color_fondo: tuple[int, int, int] | None = (255, 255, 255),
    centrar: bool = True,
) -> dict:
    with Image.open(ruta_entrada) as img:
        img = ImageOps.exif_transpose(img)
        w, h = img.size

        if w > ancho_final or h > alto_final:
            img.thumbnail((ancho_final, alto_final), Image.Resampling.LANCZOS)
            w, h = img.size

        # Transparente real solo si color_fondo es None
        if color_fondo is None:
            canvas = Image.new('RGBA', (ancho_final, alto_final), (0, 0, 0, 0))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            modo = 'RGBA' if img.mode == 'RGBA' else 'RGB'
            fondo_color = (*color_fondo, 255) if modo == 'RGBA' else color_fondo
            canvas = Image.new(modo, (ancho_final, alto_final), fondo_color)  # type: ignore

        x = (ancho_final - w) // 2 if centrar else 0
        y = (alto_final - h) // 2 if centrar else 0

        if img.mode == 'RGBA':
            canvas.paste(img, (x, y), mask=img.split()[3])
        else:
            canvas.paste(img, (x, y))

        fmt = _formato_desde_ruta(ruta_entrada)
        if fmt == 'JPEG' and canvas.mode == 'RGBA':
            canvas = canvas.convert('RGB')
        canvas.save(ruta_salida, fmt)

        return {
            'ruta_salida': ruta_salida,
            'original': (w, h),
            'resultado': (ancho_final, alto_final),
        }


def _formato_desde_ruta(ruta: str) -> str:
    ext = Path(ruta).suffix.lower()
    return {
        '.jpg': 'JPEG', '.jpeg': 'JPEG',
        '.png': 'PNG', '.webp': 'WEBP',
        '.bmp': 'BMP', '.tiff': 'TIFF',
        '.gif': 'GIF',
    }.get(ext, 'JPEG')


def any_supports_transparency(rutas: list[str]) -> bool:
    return any(Path(r).suffix.lower() in TRANSPARENCY_EXTS for r in rutas)


def canvas_color_for_choice(choice_key: str, supports_transparency: bool) -> tuple[tuple[int, int, int] | None, bool]:
    """
    choice_key: 'white' | 'black' | 'transparent'
    returns (color, fallback_used)
    """
    if choice_key == 'transparent' and supports_transparency:
        return None, False
    if choice_key == 'black' or (choice_key == 'transparent' and not supports_transparency):
        return (0, 0, 0), choice_key == 'transparent'
    return (255, 255, 255), False


def parse_dimensions(ancho_txt: str, alto_txt: str) -> tuple[int | None, int | None, str | None]:
    try:
        ancho = int(ancho_txt) if ancho_txt else None
        alto = int(alto_txt) if alto_txt else None
        return ancho, alto, None
    except ValueError:
        return None, None, 'invalid'


def batch_redimensionar(
    rutas: list[str],
    carpeta_salida: str,
    *,
    porcentaje: float | None = None,
    ancho: int | None = None,
    alto: int | None = None,
    preset_key: str | None = None,
    mantener_ratio: bool = True,
    sufijo: str = '_redim',
) -> dict:
    errores = 0
    for ruta in rutas:
        try:
            p = Path(ruta)
            salida = str(Path(carpeta_salida) / (p.stem + sufijo + p.suffix))
            redimensionar(
                ruta, salida,
                porcentaje=porcentaje,
                ancho=ancho,
                alto=alto,
                preset_key=preset_key,
                mantener_ratio=mantener_ratio,
            )
        except Exception:
            errores += 1
    return {'ok': len(rutas) - errores, 'errores': errores}


def batch_recortar(
    rutas: list[str],
    carpeta_salida: str,
    *,
    ratio: str | None = None,
    sufijo: str = '_crop',
) -> dict:
    errores = 0
    for ruta in rutas:
        try:
            p = Path(ruta)
            salida = str(Path(carpeta_salida) / (p.stem + sufijo + p.suffix))
            recortar(ruta, salida, ratio=ratio)
        except Exception:
            errores += 1
    return {'ok': len(rutas) - errores, 'errores': errores}


def batch_canvas(
    rutas: list[str],
    carpeta_salida: str,
    *,
    ancho: int,
    alto: int,
    color_fondo: tuple[int, int, int] | None,
    sufijo: str = '_canvas',
) -> dict:
    errores = 0
    for ruta in rutas:
        try:
            p = Path(ruta)
            salida = str(Path(carpeta_salida) / (p.stem + sufijo + p.suffix))
            agregar_canvas(ruta, salida, ancho, alto, color_fondo=color_fondo)
        except Exception:
            errores += 1
    return {'ok': len(rutas) - errores, 'errores': errores}
