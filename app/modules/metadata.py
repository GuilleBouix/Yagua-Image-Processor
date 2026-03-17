"""
MÃ³dulo de metadatos EXIF.
Ver, editar, limpiar y exportar metadatos de imÃ¡genes.
"""

import json
import logging
from pathlib import Path
from PIL import Image, ImageOps
import piexif

logger = logging.getLogger(__name__)


# Campos EXIF legibles con etiquetas amigables
_CAMPOS_LEGIBLES = {
    'Make':             'CÃ¡mara (marca)',
    'Model':            'CÃ¡mara (modelo)',
    'LensModel':        'Lente',
    'DateTime':         'Fecha y hora',
    'DateTimeOriginal': 'Fecha original',
    'ISO':              'ISO',
    'FNumber':          'Apertura',
    'ExposureTime':     'Velocidad obturaciÃ³n',
    'FocalLength':      'Focal',
    'Flash':            'Flash',
    'Software':         'Software',
    'Artist':           'Autor',
    'Copyright':        'Copyright',
    'ImageWidth':       'Ancho',
    'ImageLength':      'Alto',
    'GPSLatitude':      'Latitud GPS',
    'GPSLongitude':     'Longitud GPS',
}

# Campos editables por el usuario
CAMPOS_EDITABLES = {
    'Artist':    'Autor',
    'Copyright': 'Copyright',
    'Software':  'Software',
    'DateTime':  'Fecha y hora',
}


def _fraccion_a_float(val) -> float:
    """Convierte tupla (numerador, denominador) a float."""
    if isinstance(val, tuple) and len(val) == 2:
        num, den = val
        if isinstance(num, (int, float)) and isinstance(den, (int, float)) and den != 0:
            return float(num) / float(den)
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    return 0.0


def _formatear_valor(tag: str, val) -> str:
    """Convierte valores EXIF a string legible."""
    if isinstance(val, bytes):
        try:
            return val.decode('utf-8').strip('\x00')
        except Exception:
            return val.hex()

    if tag == 'FNumber':
        return f'f/{_fraccion_a_float(val):.1f}'

    if tag == 'ExposureTime':
        f = _fraccion_a_float(val)
        if f < 1:
            return f'1/{int(round(1/f))}s'
        return f'{f:.1f}s'

    if tag == 'FocalLength':
        return f'{_fraccion_a_float(val):.0f}mm'

    if tag in ('GPSLatitude', 'GPSLongitude'):
        if isinstance(val, (list, tuple)) and len(val) == 3:
            d = _fraccion_a_float(val[0])
            m = _fraccion_a_float(val[1])
            s = _fraccion_a_float(val[2])
            return f'{d:.0f}Â° {m:.0f}\' {s:.2f}"'

    if isinstance(val, tuple):
        return str(val[0]) if len(val) == 2 and val[1] == 1 else str(val)

    return str(val)


def leer_metadatos(ruta: str) -> dict[str, str]:
    """
    Lee los metadatos EXIF de una imagen.
    Retorna dict con etiqueta legible â†’ valor formateado.
    """
    resultado: dict[str, str] = {}

    try:
        with Image.open(ruta) as img:
            info = img.getexif()
        if not info:
            return resultado

        # Mapa inverso: valor numÃ©rico â†’ nombre de tag
        from PIL.ExifTags import TAGS
        tags_num = {v: k for k, v in TAGS.items()}

        for nombre, etiqueta in _CAMPOS_LEGIBLES.items():
            num = tags_num.get(nombre)
            if num and num in info:
                val = info[num]
                resultado[etiqueta] = _formatear_valor(nombre, val)

        # GPS coordinadas completas para Google Maps
        gps_info = info.get(34853)  # GPSInfo tag
        if gps_info:
            try:
                lat = _gps_a_decimal(gps_info.get(2), gps_info.get(1, 'N'))
                lon = _gps_a_decimal(gps_info.get(4), gps_info.get(3, 'E'))
                if lat and lon:
                    resultado['__gps_decimal__'] = f'{lat},{lon}'
            except Exception:
                pass

    except Exception as exc:
        logger.warning("Error al leer EXIF en %s: %s", ruta, exc)

    return resultado


def leer_metadatos_safe(ruta: str) -> tuple[dict[str, str], str | None]:
    try:
        return leer_metadatos(ruta), None
    except Exception as exc:
        return {}, str(exc)


def _gps_a_decimal(coords, ref: str) -> float | None:
    if not coords or not isinstance(coords, (list, tuple)) or len(coords) < 3:
        return None
    try:
        d = _fraccion_a_float(coords[0])
        m = _fraccion_a_float(coords[1])
        s = _fraccion_a_float(coords[2])
    except Exception:
        return None
    decimal = d + m / 60 + s / 3600
    if ref in ('S', 'W'):
        decimal = -decimal
    return round(decimal, 6)


def limpiar_exif(ruta_entrada: str, ruta_salida: str) -> dict:
    """Guarda la imagen sin ningÃºn metadato EXIF."""
    with Image.open(ruta_entrada) as img:
        img = ImageOps.exif_transpose(img)
        tam_original = Path(ruta_entrada).stat().st_size

        fmt = img.format or 'JPEG'
        img_limpia = Image.new(img.mode, img.size)
        img_limpia.paste(img)

    kwargs: dict = {}
    if fmt == 'JPEG':
        kwargs = {'quality': 95, 'optimize': True}
    elif fmt == 'PNG':
        kwargs = {'optimize': True}

    img_limpia.save(ruta_salida, fmt, **kwargs)
    tam_final = Path(ruta_salida).stat().st_size

    return {
        'ruta_salida': ruta_salida,
        'tam_original': tam_original,
        'tam_final': tam_final,
    }


def editar_exif(ruta_entrada: str, ruta_salida: str, campos: dict[str, str]) -> bool:
    """
    Edita campos EXIF especÃ­ficos y guarda la imagen.
    campos: dict con nombre_campo â†’ nuevo_valor
    """
    try:
        with Image.open(ruta_entrada) as img:
            fmt = img.format or 'JPEG'

            if fmt not in ('JPEG', 'TIFF'):
                # PNG y otros no soportan EXIF editable via piexif
                img.save(ruta_salida, fmt)
                return False

            try:
                exif_dict = piexif.load(ruta_entrada)
            except Exception:
                exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}}

            _PIEXIF_MAP = {
                'Artist':    (piexif.ImageIFD.Artist,    '0th'),
                'Copyright': (piexif.ImageIFD.Copyright, '0th'),
                'Software':  (piexif.ImageIFD.Software,  '0th'),
                'DateTime':  (piexif.ImageIFD.DateTime,  '0th'),
            }

            for campo, valor in campos.items():
                if campo in _PIEXIF_MAP:
                    tag, ifd = _PIEXIF_MAP[campo]
                    exif_dict[ifd][tag] = valor.encode('utf-8')

            exif_bytes = piexif.dump(exif_dict)
            img.save(ruta_salida, fmt, exif=exif_bytes, quality=95)
            return True

    except Exception as exc:
        logger.warning("Error al editar EXIF en %s: %s", ruta_entrada, exc)
        return False


def exportar_txt(metadatos: dict[str, str], ruta: str):
    """Exporta metadatos a archivo .txt legible."""
    lineas = ['METADATOS EXIF\n', '=' * 40 + '\n']
    for k, v in metadatos.items():
        if k.startswith('__'):
            continue
        lineas.append(f'{k:<25} {v}\n')
    Path(ruta).write_text(''.join(lineas), encoding='utf-8')


def exportar_json(metadatos: dict[str, str], ruta: str):
    """Exporta metadatos a archivo .json."""
    datos = {k: v for k, v in metadatos.items() if not k.startswith('__')}
    Path(ruta).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def exportar_metadatos(metadatos: dict[str, str], ruta: str, fmt: str) -> None:
    if fmt == 'txt':
        exportar_txt(metadatos, ruta)
    else:
        exportar_json(metadatos, ruta)


def preparar_campos_exif(
    campos_edit: dict[str, str],
) -> tuple[dict[str, str], str | None]:
    campos = {k: v for k, v in campos_edit.items() if v.strip()}
    if not campos:
        return {}, 'empty'
    return campos, None


def batch_limpiar_exif(
    rutas: list[str],
    carpeta_salida: str,
    sufijo: str = '_sinexif',
) -> dict:
    errores = 0
    for ruta in rutas:
        try:
            p = Path(ruta)
            salida = str(Path(carpeta_salida) / (p.stem + sufijo + p.suffix))
            limpiar_exif(ruta, salida)
        except Exception:
            errores += 1
    return {'ok': len(rutas) - errores, 'errores': errores}
