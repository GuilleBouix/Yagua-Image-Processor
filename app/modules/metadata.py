"""
Modulo de metadatos EXIF.
Ver, editar, limpiar y exportar metadatos de imagenes.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/metadata/services.py: Usa las funciones de este modulo.
"""

from types import MappingProxyType
from typing import Mapping, cast
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
import json
from copy import deepcopy
import shutil
import logging
import math
from pathlib import Path

from PIL import Image, ImageOps
import piexif
from piexif import helper as piexif_helper

from app.utils.output import unique_output_path, safe_image_output, atomic_destination, require_single_frame, atomic_write_text

from app.utils.results import FileFailure, file_failure
from app.utils.saving import canonical_format
from app.utils.image_source import primary_jpeg_bytes

logger = logging.getLogger(__name__)


class _TiffExifText(str):

    """Conserva bytes originales mientras Pillow determina el tipo ASCII EXIF.

    Los bytes simples pueden hacer que Pillow infiera BYTE en etiquetas EXIF anidadas.
    Las cadenas normales tampoco sirven aquí: para UserComment TIFF indefinido se
    necesita codificar el contenido subyacente sin perder su tipo de etiqueta."""

    def encode(self, encoding: str = 'utf-8', errors: str = 'strict') -> bytes:
        """Codifica el texto según el flujo de escritura TIFF de piexif."""
        if encoding == 'ascii' and errors == 'replace':
            return super().encode('latin-1')
        return super().encode(encoding, errors)


# Campos EXIF legibles con etiquetas amigables
_CAMPOS_LEGIBLES = {
    'Make':             'Camara (marca)',
    'Model':            'Camara (modelo)',
    'LensModel':        'Lente',
    'DateTime':         'Fecha y hora',
    'DateTimeOriginal': 'Fecha original',
    'DateTimeDigitized': 'Fecha digitalizada',
    'ISOSpeedRatings':  'ISO',
    'FNumber':          'Apertura',
    'ExposureTime':     'Velocidad obturacion',
    'FocalLength':      'Focal',
    'Flash':            'Flash',
    'Software':         'Software',
    'Artist':           'Autor',
    'Copyright':        'Copyright',
    'ImageWidth':       'Ancho',
    'ImageLength':      'Alto',
    'GPSLatitude':      'Latitud GPS',
    'GPSLongitude':     'Longitud GPS',
    'ImageDescription': 'Descripcion de imagen',
    'UserComment':      'Comentario',
    'LensMake':         'Lente (marca)',
    'FocalLengthIn35mmFilm': 'Focal equivalente 35 mm',
    'ExposureProgram':  'Programa de exposicion',
    'ExposureMode':     'Modo de exposicion',
    'ExposureBiasValue': 'Compensacion de exposicion',
    'MeteringMode':     'Medicion de luz',
    'WhiteBalance':     'Balance de blancos',
    'LightSource':      'Fuente de luz',
    'GPSAltitude':      'Altitud GPS',
    'GPSImgDirection':  'Direccion GPS',
    'Orientation':      'Orientacion',
    'ColorSpace':       'Espacio de color',
}

# Grupos y claves de traducción que describen las opciones del editor.
GRUPOS_CAMPOS_EDITABLES = {
    'description': ('ImageDescription', 'Artist', 'Copyright', 'UserComment', 'Software'),
    'camera': ('Make', 'Model', 'LensMake', 'LensModel'),
    'capture': (
        'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength',
        'FocalLengthIn35mmFilm', 'ExposureProgram', 'ExposureMode',
        'ExposureBiasValue', 'MeteringMode', 'Flash', 'WhiteBalance', 'LightSource',
    ),
    'gps': ('GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection'),
}
CAMPOS_EDITABLES = {
    'ImageDescription': 'image_description',
    'Artist': 'artist',
    'Copyright': 'copyright',
    'UserComment': 'user_comment',
    'Software': 'software',
    'Make': 'camera_make',
    'Model': 'camera_model',
    'LensMake': 'lens_make',
    'LensModel': 'lens_model',
    'DateTimeOriginal': 'capture_date',
    'ExposureTime': 'exposure_time',
    'FNumber': 'aperture',
    'ISOSpeedRatings': 'iso',
    'FocalLength': 'focal_length',
    'FocalLengthIn35mmFilm': 'focal_length_35mm',
    'ExposureProgram': 'exposure_program',
    'ExposureMode': 'exposure_mode',
    'ExposureBiasValue': 'exposure_bias',
    'MeteringMode': 'metering_mode',
    'Flash': 'flash',
    'WhiteBalance': 'white_balance',
    'LightSource': 'light_source',
    'GPSLatitude': 'gps_latitude',
    'GPSLongitude': 'gps_longitude',
    'GPSAltitude': 'gps_altitude',
    'GPSImgDirection': 'gps_direction',
}

# El visor reutiliza los campos y grupos del editor; las claves de exportación
# existentes permanecen estables aunque las etiquetas de la UI se traduzcan.
GRUPOS_CAMPOS_VISIBLES = {
    **GRUPOS_CAMPOS_EDITABLES,
    'dates': ('DateTimeOriginal', 'DateTime', 'DateTimeDigitized'),
    'orientation': ('ImageWidth', 'ImageLength', 'Orientation', 'ColorSpace'),
}
_TRADUCCIONES_VISIBLES = {
    **CAMPOS_EDITABLES,
    'DateTime': 'datetime',
    'DateTimeDigitized': 'metadata_date_digitized',
    'ImageWidth': 'width',
    'ImageLength': 'height',
    'Orientation': 'current_orientation',
    'ColorSpace': 'color_space',
}
CAMPOS_VISIBLES = {
    nombre: (etiqueta, _TRADUCCIONES_VISIBLES[nombre])
    for nombre, etiqueta in _CAMPOS_LEGIBLES.items()
}
_TAGS_VISIBLES = {
    detalle['name']: (tag, grupo)
    for grupo in ('0th', 'Exif', 'GPS')
    for tag, detalle in piexif.TAGS[grupo].items()
    if detalle['name'] in CAMPOS_VISIBLES
}


OPCIONES_ENUM_EXIF = {
    'ExposureProgram': {
        0: 'enum_not_defined', 1: 'enum_manual', 2: 'enum_program',
        3: 'enum_aperture_priority', 4: 'enum_shutter_priority',
        5: 'enum_creative', 6: 'enum_action', 7: 'enum_portrait', 8: 'enum_landscape',
    },
    'ExposureMode': {0: 'enum_auto', 1: 'enum_manual', 2: 'enum_auto_bracket'},
    'MeteringMode': {
        0: 'enum_meter_unknown', 1: 'enum_average', 2: 'enum_center_weighted',
        3: 'enum_spot', 4: 'enum_multi_spot', 5: 'enum_pattern',
        6: 'enum_partial', 255: 'enum_other',
    },
    'Flash': {0: 'flash_no', 1: 'flash_yes'},
    'WhiteBalance': {0: 'wb_auto', 1: 'wb_manual'},
    'LightSource': {
        0: 'enum_not_defined', 1: 'light_daylight', 2: 'light_fluorescent',
        3: 'light_tungsten', 4: 'light_flash', 9: 'light_fine_weather',
        10: 'light_cloudy', 11: 'light_shade', 255: 'enum_other',
    },
}
ORIENTACIONES_EXIF = {
    1: 'orient_normal', 2: 'orient_mirror_horizontal', 3: 'orient_180',
    4: 'orient_mirror_vertical', 5: 'orient_transpose', 6: 'orient_90_cw',
    7: 'orient_transverse', 8: 'orient_90_ccw',
}


@dataclass(frozen=True)
class MetadataEditRequest:
    """Valores EXIF validados y acciones opcionales solicitadas por la UI."""

    values: Mapping[str, str | int | float | tuple[int, int]]
    sync_dates: bool = False
    clear_gps: bool = False
    orientation: int | None = None

    def __post_init__(self):
        """Congela los valores recibidos para evitar cambios durante el guardado."""
        object.__setattr__(self, 'values', MappingProxyType(dict(self.values)))


_TEXT_TAGS = {
    'ImageDescription': (piexif.ImageIFD.ImageDescription, '0th'),
    'Artist': (piexif.ImageIFD.Artist, '0th'),
    'Copyright': (piexif.ImageIFD.Copyright, '0th'),
    'Software': (piexif.ImageIFD.Software, '0th'),
    'Make': (piexif.ImageIFD.Make, '0th'),
    'Model': (piexif.ImageIFD.Model, '0th'),
    'DateTime': (piexif.ImageIFD.DateTime, '0th'),
    'DateTimeOriginal': (piexif.ExifIFD.DateTimeOriginal, 'Exif'),
    'DateTimeDigitized': (piexif.ExifIFD.DateTimeDigitized, 'Exif'),
    'LensMake': (piexif.ExifIFD.LensMake, 'Exif'),
    'LensModel': (piexif.ExifIFD.LensModel, 'Exif'),
}
_USER_COMMENT_TAG = (piexif.ExifIFD.UserComment, 'Exif')
_RATIONAL_TAGS = {
    'ExposureTime': (piexif.ExifIFD.ExposureTime, 'Exif', True),
    'FNumber': (piexif.ExifIFD.FNumber, 'Exif', True),
    'FocalLength': (piexif.ExifIFD.FocalLength, 'Exif', True),
    'ExposureBiasValue': (piexif.ExifIFD.ExposureBiasValue, 'Exif', False),
}
_INTEGER_TAGS = {
    'ISOSpeedRatings': (piexif.ExifIFD.ISOSpeedRatings, 'Exif', True),
    'FocalLengthIn35mmFilm': (piexif.ExifIFD.FocalLengthIn35mmFilm, 'Exif', True),
}
_ENUM_TAGS = {
    'ExposureProgram': (piexif.ExifIFD.ExposureProgram, 'Exif', set(range(9))),
    'ExposureMode': (piexif.ExifIFD.ExposureMode, 'Exif', {0, 1, 2}),
    'MeteringMode': (piexif.ExifIFD.MeteringMode, 'Exif', {0, 1, 2, 3, 4, 5, 6, 255}),
    'Flash': (piexif.ExifIFD.Flash, 'Exif', {0, 1}),
    'WhiteBalance': (piexif.ExifIFD.WhiteBalance, 'Exif', {0, 1}),
    'LightSource': (piexif.ExifIFD.LightSource, 'Exif', {0, 1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 255}),
}
_DATE_FORMATS = (
    '%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M',
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
    '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
)


def _fraccion_a_float(val):
    """Acepta números, racionales de Pillow y pares numerador/denominador."""
    if isinstance(val, tuple) and len(val) == 2:
        number = float(val[0]) / float(val[1])
    else:
        number = float(cast(str | int | float, val))
    if not math.isfinite(number):
        raise ValueError('Racional EXIF no finito')
    return number


def _formatear_valor(nombre_tag, val):
    """Devuelve texto legible sin descartar valores cero."""
    if nombre_tag == 'UserComment' and isinstance(val, bytes):
        try:
            return piexif_helper.UserComment.load(val).strip('\x00')
        except (ValueError, UnicodeError):
            prefixes = (b'ASCII\x00\x00\x00', b'UNICODE\x00', b'JIS\x00\x00\x00\x00\x00')
            payload = val[8:] if val.startswith(prefixes) else val
            return payload.decode('utf-8', errors='replace').strip('\x00')
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace').strip('\x00')
    if isinstance(val, str):
        # Pillow interpreta varios textos EXIF como Latin-1, incluso cuando
        # fueron escritos en UTF-8 por Yagua.
        try:
            return val.encode('latin-1').decode('utf-8').strip('\x00')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return val.strip('\x00')
    if nombre_tag == 'FNumber':
        return f'f/{_fraccion_a_float(val):g}'
    if nombre_tag == 'ExposureTime':
        seconds = _fraccion_a_float(val)
        if 0 < seconds < 1:
            reciprocal = 1 / seconds
            if math.isclose(reciprocal, round(reciprocal), rel_tol=1e-6):
                return f'1/{round(reciprocal)}s'
        return f'{seconds:g}s'
    if nombre_tag in ('FocalLength', 'FocalLengthIn35mmFilm'):
        return f'{_fraccion_a_float(val):g}mm'
    if nombre_tag == 'ExposureBiasValue':
        return f'{_fraccion_a_float(val):g} EV'
    if nombre_tag == 'GPSAltitude':
        return f'{_fraccion_a_float(val):g} m'
    if nombre_tag == 'GPSImgDirection':
        return f'{_fraccion_a_float(val):g}°'
    if nombre_tag in ('GPSLatitude', 'GPSLongitude'):
        if not isinstance(val, (list, tuple)) or len(val) != 3:
            raise ValueError('Coordenada EXIF inválida')
        degrees, minutes, seconds = (_fraccion_a_float(part) for part in val)
        return f'{degrees:g}° {minutes:g}\' {seconds:.2f}"'
    if isinstance(val, tuple) and len(val) == 2:
        return f'{_fraccion_a_float(val):g}'
    return str(val)


def leer_metadatos(ruta):
    """Lee los campos conocidos y devuelve las claves planas históricas."""
    logger.info("Leer metadatos: %s", ruta)
    resultado = {}
    try:
        with Image.open(ruta) as imagen:
            info = imagen.getexif()
            if not info:
                return resultado
            bloques = {'0th': info, 'Exif': {}, 'GPS': {}}
            for grupo, tag in (('Exif', 34665), ('GPS', 34853)):
                try:
                    bloques[grupo] = info.get_ifd(tag)
                except Exception as exc:
                    logger.warning("No se pudo leer el bloque EXIF %s: %s", grupo, exc)
            for nombre, (etiqueta, _) in CAMPOS_VISIBLES.items():
                try:
                    tag, grupo = _TAGS_VISIBLES[nombre]
                    valor = bloques[grupo].get(tag)
                    if valor is None and nombre in ('ImageWidth', 'ImageLength'):
                        dimension_tag = 40962 if nombre == 'ImageWidth' else 40963
                        valor = bloques['Exif'].get(dimension_tag)
                    if valor is None:
                        continue
                    if nombre == 'GPSAltitude' and bloques['GPS'].get(5) == 1:
                        valor = -_fraccion_a_float(valor)
                    texto = _formatear_valor(nombre, valor)
                    if not texto.strip():
                        continue
                    if nombre in ('GPSLatitude', 'GPSLongitude'):
                        reference_tag = 1 if nombre == 'GPSLatitude' else 3
                        referencia = _gps_referencia(bloques['GPS'], reference_tag, '')
                        if referencia:
                            texto += ' ' + referencia
                    resultado[etiqueta] = texto
                except Exception as exc:
                    logger.warning("Se omitió el campo EXIF %s: %s", nombre, exc)
            gps = bloques['GPS']
            latitud = _gps_a_decimal(gps.get(2), _gps_referencia(gps, 1, 'N'))
            longitud = _gps_a_decimal(gps.get(4), _gps_referencia(gps, 3, 'E'))
            if latitud is not None and longitud is not None:
                resultado['__gps_decimal__'] = f'{latitud},{longitud}'
    except Exception as exc:
        logger.warning("Error al leer EXIF en %s: %s", ruta, exc)
    return resultado


def _decimal_texto(valor):
    """Devuelve una representacion compacta para editar valores racionales."""
    if isinstance(valor, tuple) and len(valor) == 2 and valor[1]:
        numero = valor[0] / valor[1]
    else:
        numero = valor
    return f'{float(cast(str | int | float, numero)):.8f}'.rstrip('0').rstrip('.')


def _gps_referencia(gps, tag, defecto):
    """Lee la referencia cardinal de una etiqueta GPS y aplica su valor inicial."""
    referencia = gps.get(tag, defecto)
    return referencia.decode('ascii', errors='ignore') if isinstance(referencia, bytes) else str(referencia)


def leer_campos_edicion(ruta):
    """Lee los valores EXIF editables sin convertirlos a etiquetas de vista."""
    with Image.open(ruta) as imagen:
        tamano = imagen.size
        exif = piexif.load(ruta)

    resultado = {'__image_size__': f'{tamano[0]} x {tamano[1]}'}
    for nombre, (tag, ifd) in _TEXT_TAGS.items():
        valor = exif.get(ifd, {}).get(tag)
        if valor:
            resultado[nombre] = valor.decode('utf-8', errors='replace').rstrip('\x00')

    valor = exif.get('Exif', {}).get(_USER_COMMENT_TAG[0])
    if valor:
        valor_bytes = valor if isinstance(valor, bytes) else bytes(valor)
        try:
            resultado['UserComment'] = piexif_helper.UserComment.load(valor_bytes)
        except (ValueError, UnicodeError):
            resultado['UserComment'] = valor_bytes.decode('utf-8', errors='replace').rstrip('\x00')

    for nombre, (tag, ifd, _positivo) in _RATIONAL_TAGS.items():
        valor = exif.get(ifd, {}).get(tag)
        if valor:
            resultado[nombre] = _decimal_texto(valor)
    for nombre, (tag, ifd, _positivo) in _INTEGER_TAGS.items():
        valor = exif.get(ifd, {}).get(tag)
        if valor is not None:
            resultado[nombre] = str(valor)
    for nombre, (tag, ifd, _opciones) in _ENUM_TAGS.items():
        valor = exif.get(ifd, {}).get(tag)
        if valor is not None:
            resultado[nombre] = str(valor)

    gps = exif.get('GPS', {})
    if gps:
        lat = _gps_a_decimal(
            gps.get(piexif.GPSIFD.GPSLatitude),
            _gps_referencia(gps, piexif.GPSIFD.GPSLatitudeRef, b'N'),
        )
        lon = _gps_a_decimal(
            gps.get(piexif.GPSIFD.GPSLongitude),
            _gps_referencia(gps, piexif.GPSIFD.GPSLongitudeRef, b'E'),
        )
        if lat is not None and lon is not None:
            resultado['GPSLatitude'] = str(lat)
            resultado['GPSLongitude'] = str(lon)
        altitude = gps.get(piexif.GPSIFD.GPSAltitude)
        if altitude:
            resultado['GPSAltitude'] = _decimal_texto(altitude)
            if gps.get(piexif.GPSIFD.GPSAltitudeRef, 0) == 1:
                resultado['GPSAltitude'] = f"-{resultado['GPSAltitude']}"
        direction = gps.get(piexif.GPSIFD.GPSImgDirection)
        if direction:
            resultado['GPSImgDirection'] = _decimal_texto(direction)

    with Image.open(ruta) as imagen:
        color_space = imagen.getexif().get(piexif.ExifIFD.ColorSpace)
    resultado['__color_space__'] = str(color_space) if color_space is not None else ''
    resultado['__orientation__'] = str(exif.get('0th', {}).get(piexif.ImageIFD.Orientation, 1))
    return resultado


def leer_campos_edicion_safe(ruta):
    """Versión segura de :func:`leer_campos_edicion` para la interfaz."""
    try:
        return leer_campos_edicion(ruta), None
    except Exception as exc:
        logger.warning("Error al leer campos editables EXIF en %s: %s", ruta, exc)
        return {}, str(exc)


def leer_metadatos_safe(ruta):
    """
    Wrapper seguro para leer_metadatos que maneja errores.
    
    Args:
        ruta: Ruta de la imagen.
        
    Returns:
        Tupla (diccionario, mensaje_error). Si hay exito, error es None.
    """
    try:
        return leer_metadatos(ruta), None
    except Exception as exc:
        return {}, str(exc)


def _gps_a_decimal(coordenadas, referencia_gps):
    """
    Convierte coordenadas GPS a formato decimal.
    
    Args:
        coordenadas: Tupla (grados, minutos, segundos).
        referencia_gps: Referencia 'N', 'S', 'E' o 'W'.
        
    Returns:
        Coordenada en grados decimales o None si falla.
    """
    if not coordenadas or not isinstance(coordenadas, (list, tuple)) or len(coordenadas) < 3:
        return None
    try:
        grados = _fraccion_a_float(coordenadas[0])
        minutos = _fraccion_a_float(coordenadas[1])
        segundos = _fraccion_a_float(coordenadas[2])
    except Exception:
        return None
    
    # Convertir a grados decimales
    decimal = grados + minutos / 60 + segundos / 3600
    
    # Aplicar signo negativo para sur y oeste
    if isinstance(referencia_gps, bytes):
        referencia_gps = referencia_gps.decode('ascii', errors='ignore')
    if str(referencia_gps).strip().upper() in ('S', 'W'):
        decimal = -decimal
    
    return round(decimal, 6)


@safe_image_output
def limpiar_exif(ruta_entrada, ruta_salida):
    """
    Guarda la imagen sin ningun metadato EXIF.
    
    Crea una nueva imagen copiando solo los datos de pixel
    sin ninguna metadata.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen limpia.
        
    Returns:
        Diccionario con tamanos original y final.
    """

    logger.info("Limpiar EXIF: %s -> %s", ruta_entrada, ruta_salida)
    with Image.open(ruta_entrada) as imagen:
        formato = canonical_format(imagen.format or 'JPEG')
        imagen = ImageOps.exif_transpose(imagen)
        tam_original = Path(ruta_entrada).stat().st_size

        # Crear nueva imagen copiando solo los pixeles
        img_limpia = Image.new(imagen.mode, imagen.size)
        img_limpia.paste(imagen)

    # Guardar sin EXIF
    argumentos_guardado = {}
    if formato == 'JPEG':
        argumentos_guardado = {'quality': 95, 'optimize': True}
    elif formato == 'PNG':
        argumentos_guardado = {'optimize': True}

    img_limpia.save(ruta_salida, formato, **argumentos_guardado)
    tam_final = Path(ruta_salida).stat().st_size

    return {
        'ruta_salida': ruta_salida,
        'tam_original': tam_original,
        'tam_final': tam_final,
    }


def _rational(valor):
    """Convierte un número a la fracción racional que espera piexif."""
    fraccion = Fraction(str(valor)).limit_denominator(1_000_000)
    return fraccion.numerator, fraccion.denominator


def _gps_tags(latitud, longitud):
    """Codifica coordenadas decimales y sus referencias en etiquetas GPS EXIF."""
    def _coordenada(valor):
        """Descompone grados decimales en tres fracciones EXIF."""
        total_segundos = round(abs(valor) * 3600 * 1_000_000)
        grados, resto = divmod(total_segundos, 3600 * 1_000_000)
        minutos, microsegundos = divmod(resto, 60 * 1_000_000)
        return ((grados, 1), (minutos, 1), (microsegundos, 1_000_000))

    return {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b'S' if latitud < 0 else b'N',
        piexif.GPSIFD.GPSLatitude: _coordenada(latitud),
        piexif.GPSIFD.GPSLongitudeRef: b'W' if longitud < 0 else b'E',
        piexif.GPSIFD.GPSLongitude: _coordenada(longitud),
    }


def editar_exif(ruta_entrada, ruta_salida, request):
    """Escribe los cambios EXIF en una salida segura y devuelve su estado."""
    try:
        require_single_frame(ruta_entrada)
        source = Path(ruta_entrada)
        before = source.stat()
        destination = Path(ruta_salida)
        same_file = source.resolve() == destination.resolve()
        # Una excepción privada cancela la publicación cuando hay un fallo o no hay cambios.
        with atomic_destination(destination, replace=same_file) as temporary:
            ok, warning = _editar_exif(str(source), str(temporary), request)
            if not ok:
                raise _EditAborted(warning)
            if warning == 'unchanged':
                if same_file:
                    raise _EditAborted('unchanged')
                shutil.copyfile(source, temporary)
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise OSError('source_changed')
        return True, None
    except _EditAborted as error:
        return (True, None) if str(error) == 'unchanged' else (False, str(error))
    except Exception as error:
        logger.warning('EXIF save aborted: %s', error)
        return False, 'unsupported_frames' if str(error) == 'unsupported_frames' else 'error'


class _EditAborted(Exception):
    """Indica que no se debe publicar una salida por falta de cambios aplicables."""

    pass


def _editar_exif(ruta_entrada, ruta_salida, request):
    """
    Edita campos EXIF especificos y guarda la imagen.
    
    Solo soporta JPEG y TIFF que tienen soporte EXIF real.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen editada.
        request: Solicitud validada de edición EXIF.
        
    Returns:
        Tupla (ok, warning). Si ok es True pero warning no es None, la
        imagen se guardo sin EXIF por formato no compatible.
    """

    if isinstance(request, dict):
        request = MetadataEditRequest(request)

    logger.info("Editar EXIF: %s -> %s", ruta_entrada, ruta_salida)
    try:
        with Image.open(ruta_entrada) as imagen:
            formato = canonical_format(imagen.format or 'JPEG')

            # Solo JPEG y TIFF soportan EXIF editable
            if formato not in ('JPEG', 'TIFF'):
                return False, 'no_exif'

            exif_dict = piexif.load(str(ruta_entrada))
            # Pillow puede guardar UserComment TIFF como BYTE; piexif lo lee como una
            # tupla, pero necesita bytes al serializar la etiqueta EXIF UNDEFINED.
            comentario = exif_dict['Exif'].get(piexif.ExifIFD.UserComment)
            if isinstance(comentario, tuple):
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = bytes(comentario)
            original_exif = deepcopy(exif_dict)

            if request.clear_gps:
                exif_dict['GPS'] = {}

            for campo, valor in request.values.items():
                if campo in _TEXT_TAGS:
                    nombre_tag, ifd = _TEXT_TAGS[campo]
                    exif_dict[ifd][nombre_tag] = cast(str, valor).encode('utf-8')
                elif campo == 'UserComment':
                    nombre_tag, ifd = _USER_COMMENT_TAG
                    exif_dict[ifd][nombre_tag] = piexif_helper.UserComment.dump(
                        str(valor), encoding='unicode'
                    )
                elif campo in _RATIONAL_TAGS:
                    nombre_tag, ifd, _positivo = _RATIONAL_TAGS[campo]
                    exif_dict[ifd][nombre_tag] = valor
                elif campo in _INTEGER_TAGS:
                    nombre_tag, ifd, _positivo = _INTEGER_TAGS[campo]
                    exif_dict[ifd][nombre_tag] = valor
                elif campo in _ENUM_TAGS:
                    nombre_tag, ifd, _opciones = _ENUM_TAGS[campo]
                    exif_dict[ifd][nombre_tag] = valor

            if request.sync_dates and 'DateTimeOriginal' in request.values:
                fecha = cast(str, request.values['DateTimeOriginal']).encode('utf-8')
                exif_dict['0th'][piexif.ImageIFD.DateTime] = fecha
                exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = fecha

            gps_values = request.values
            if 'GPSLatitude' in gps_values and not request.clear_gps:
                latitud = float(cast(str | int | float, gps_values['GPSLatitude']))
                longitud = float(cast(str | int | float, gps_values['GPSLongitude']))
                exif_dict['GPS'].update(_gps_tags(latitud, longitud))
                if 'GPSAltitude' in gps_values:
                    altitud = float(cast(str | int | float, gps_values['GPSAltitude']))
                    exif_dict['GPS'][piexif.GPSIFD.GPSAltitude] = _rational(abs(altitud))
                    exif_dict['GPS'][piexif.GPSIFD.GPSAltitudeRef] = int(altitud < 0)
                if 'GPSImgDirection' in gps_values:
                    exif_dict['GPS'][piexif.GPSIFD.GPSImgDirectionRef] = b'T'
                    exif_dict['GPS'][piexif.GPSIFD.GPSImgDirection] = _rational(
                        float(cast(str | int | float, gps_values['GPSImgDirection']))
                    )

            if request.orientation is not None:
                image = ImageOps.exif_transpose(imagen)
                orientation_transforms = {
                    1: None,
                    2: Image.Transpose.FLIP_LEFT_RIGHT,
                    3: Image.Transpose.ROTATE_180,
                    4: Image.Transpose.FLIP_TOP_BOTTOM,
                    5: Image.Transpose.TRANSPOSE,
                    6: Image.Transpose.ROTATE_270,
                    7: Image.Transpose.TRANSVERSE,
                    8: Image.Transpose.ROTATE_90,
                }
                transform = orientation_transforms[request.orientation]
                if transform is not None:
                    image = image.transpose(transform)
                exif_dict['0th'][piexif.ImageIFD.Orientation] = 1
                exif_dict['0th'][piexif.ImageIFD.ImageWidth] = image.width
                exif_dict['0th'][piexif.ImageIFD.ImageLength] = image.height
                if formato == 'JPEG':
                    exif_dict['Exif'][piexif.ExifIFD.PixelXDimension] = image.width
                    exif_dict['Exif'][piexif.ExifIFD.PixelYDimension] = image.height
            else:
                image = imagen

            if request.orientation is None and original_exif == exif_dict:
                return True, 'unchanged'

            # Guardar con EXIF modificado
            if formato == 'TIFF':
                # Pillow reconstruye estas etiquetas de almacenamiento al transformar los píxeles.
                for tag in (
                    piexif.ImageIFD.ImageWidth,
                    piexif.ImageIFD.ImageLength,
                    piexif.ImageIFD.BitsPerSample,
                    piexif.ImageIFD.Compression,
                    piexif.ImageIFD.PhotometricInterpretation,
                    piexif.ImageIFD.StripOffsets,
                    piexif.ImageIFD.SamplesPerPixel,
                    piexif.ImageIFD.RowsPerStrip,
                    piexif.ImageIFD.StripByteCounts,
                    piexif.ImageIFD.PlanarConfiguration,
                ):
                    exif_dict['0th'].pop(tag, None)
            exif_bytes = piexif.dump(exif_dict)
            if formato == 'JPEG' and request.orientation is None:
                # Reemplaza solo APP1: no decodifica ni recomprime los datos de imagen JPEG.
                source_bytes = primary_jpeg_bytes(ruta_entrada) if imagen.format == 'MPO' else Path(ruta_entrada).read_bytes()
                piexif.insert(exif_bytes, source_bytes, str(ruta_salida))
                return True, None
            opciones_guardado: dict[str, object] = {'exif': exif_bytes}
            if formato == 'TIFF':
                exif_tiff = Image.Exif()
                exif_tiff.load(exif_bytes)
                # Pillow convierte a ASCII con reemplazo las cadenas TIFF leídas.
                # Restaura los bytes originales sin cambiar el tipo de etiqueta ASCII.
                for tag, bloque in _TEXT_TAGS.values():
                    if tag in exif_dict[bloque]:
                        destino = exif_tiff if bloque == '0th' else exif_tiff.get_ifd(34665)
                        destino[tag] = _TiffExifText(exif_dict[bloque][tag].decode('latin-1'))
                opciones_guardado['exif'] = exif_tiff
            if imagen.info.get('icc_profile'):
                opciones_guardado['icc_profile'] = imagen.info['icc_profile']
            if formato == 'JPEG':
                opciones_guardado['quality'] = 95
            image.save(ruta_salida, formato, **opciones_guardado)
            return True, None

    except Exception as exc:
        logger.warning("Error al editar EXIF en %s: %s", ruta_entrada, exc)
        return False, 'error'


def exportar_txt(metadatos, ruta):
    """
    Exporta metadatos a archivo de texto legible.
    
    Args:
        metadatos: Diccionario de metadatos.
        ruta: Ruta del archivo .txt a crear.
    """
    lineas = ['METADATOS EXIF\n', '=' * 40 + '\n']
    for clave, valor in metadatos.items():
        # Ignorar campos internos (los que empiezan con __)
        if clave.startswith('__'):
            continue
        lineas.append(f'{clave:<25} {valor}\n')
    atomic_write_text(ruta, ''.join(lineas))


def exportar_json(metadatos, ruta):
    """
    Exporta metadatos a archivo JSON.
    
    Args:
        metadatos: Diccionario de metadatos.
        ruta: Ruta del archivo .json a crear.
    """
    # Filtrar campos internos
    datos = {
        clave: valor
        for clave, valor in metadatos.items()
        if not clave.startswith('__')
    }
    atomic_write_text(ruta, json.dumps(datos, ensure_ascii=False, indent=2))


def exportar_metadatos(metadatos, ruta, formato):
    """
    Exporta metadatos al formato especificado.
    
    Args:
        metadatos: Diccionario de metadatos.
        ruta: Ruta del archivo a crear.
        formato: Formato de exportacion ('txt' o 'json').
    """
    if formato == 'txt':
        exportar_txt(metadatos, ruta)
    else:
        exportar_json(metadatos, ruta)


def preparar_campos_exif(
    campos_edit,
    *,
    sync_dates=False,
    clear_gps=False,
    orientation=None,
):
    """
    Prepara los campos editados para guardar.
    
    Filtra campos vacios y valida que haya algo que guardar.
    
    Args:
        campos_edit: Diccionario con campos a editar.
        
    Returns:
        Tupla (solicitud validada, error). Si error es None, exito.
    """
    valores = {}
    claves_conocidas = set(_TEXT_TAGS) | {'UserComment'} | set(_RATIONAL_TAGS) | set(_INTEGER_TAGS) | set(_ENUM_TAGS) | {
        'GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection'
    }
    if set(campos_edit) - claves_conocidas:
        return None, 'invalid_field'

    campos = {clave: str(valor).strip() for clave, valor in campos_edit.items()}
    campos = {clave: valor for clave, valor in campos.items() if valor}
    for campo_fecha in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
        if campo_fecha not in campos:
            continue
        for formato in _DATE_FORMATS:
            try:
                fecha = datetime.strptime(campos[campo_fecha], formato)
                campos[campo_fecha] = (
                    f'{fecha.year:04}:{fecha.month:02}:{fecha.day:02} '
                    f'{fecha.hour:02}:{fecha.minute:02}:{fecha.second:02}'
                )
                break
            except ValueError:
                continue
        else:
            return None, 'invalid_date'

    for nombre, valor in campos.items():
        if nombre in _TEXT_TAGS or nombre == 'UserComment':
            valores[nombre] = valor
        elif nombre in _RATIONAL_TAGS:
            _tag, _ifd, positivo = _RATIONAL_TAGS[nombre]
            try:
                numero = Fraction(valor)
                if positivo and numero <= 0:
                    return None, 'invalid_number'
                rational = _rational(numero)
                lower, upper = (-(2**31), 2**31 - 1) if nombre == 'ExposureBiasValue' else (0, 2**32 - 1)
                if not lower <= rational[0] <= upper or not 1 <= rational[1] <= upper:
                    return None, 'invalid_number'
                valores[nombre] = rational
            except (ValueError, ZeroDivisionError):
                return None, 'invalid_number'
        elif nombre in _INTEGER_TAGS:
            _tag, _ifd, positivo = _INTEGER_TAGS[nombre]
            try:
                numero = int(valor)
                if str(numero) != valor or not 0 <= numero <= 65535 or (positivo and numero <= 0):
                    return None, 'invalid_number'
                valores[nombre] = numero
            except ValueError:
                return None, 'invalid_number'
        elif nombre in _ENUM_TAGS:
            _tag, _ifd, opciones = _ENUM_TAGS[nombre]
            try:
                numero = int(valor)
                if str(numero) != valor or numero not in opciones:
                    return None, 'invalid_option'
                valores[nombre] = numero
            except ValueError:
                return None, 'invalid_option'

    gps_fields = {'GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection'}
    campos_gps = gps_fields & set(campos)
    if clear_gps and campos_gps:
        return None, 'gps_conflict'
    has_lat = 'GPSLatitude' in campos
    has_lon = 'GPSLongitude' in campos
    if has_lat != has_lon or (campos_gps - {'GPSLatitude', 'GPSLongitude'} and not (has_lat and has_lon)):
        return None, 'gps_pair'
    if has_lat and has_lon:
        try:
            latitud = float(campos['GPSLatitude'])
            longitud = float(campos['GPSLongitude'])
            if not math.isfinite(latitud) or not -90 <= latitud <= 90:
                return None, 'invalid_gps'
            if not math.isfinite(longitud) or not -180 <= longitud <= 180:
                return None, 'invalid_gps'
            valores['GPSLatitude'] = f'{latitud:.8f}'.rstrip('0').rstrip('.')
            valores['GPSLongitude'] = f'{longitud:.8f}'.rstrip('0').rstrip('.')
            if 'GPSAltitude' in campos:
                altitud = float(campos['GPSAltitude'])
                if not math.isfinite(altitud) or _rational(abs(altitud))[0] > 2**32 - 1:
                    return None, 'invalid_gps'
                valores['GPSAltitude'] = altitud
            if 'GPSImgDirection' in campos:
                direccion = float(campos['GPSImgDirection'])
                if not math.isfinite(direccion) or not 0 <= direccion < 360:
                    return None, 'invalid_gps'
                valores['GPSImgDirection'] = direccion
        except ValueError:
            return None, 'invalid_gps'

    if sync_dates and 'DateTimeOriginal' not in valores:
        return None, 'sync_requires_date'
    if orientation is not None:
        try:
            orientation = int(orientation)
        except (TypeError, ValueError):
            return None, 'invalid_orientation'
        if orientation not in range(1, 9):
            return None, 'invalid_orientation'

    if not valores and not clear_gps and orientation is None:
        return None, 'empty'
    return MetadataEditRequest(valores, sync_dates, clear_gps, orientation), None


def batch_limpiar_exif(rutas, carpeta_salida, sufijo='_sinexif'):
    """
    Limpia metadatos EXIF de multiples imagenes.
    
    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar las imagenes.
        sufijo: Sufijo para agregar al nombre de archivo.
        
    Returns:
        Diccionario con exitos, errores y conflictos.
    """
    fallos: list[FileFailure] = []

    logger.info("Batch limpiar EXIF: %s archivos -> %s", len(rutas), carpeta_salida)
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
            limpiar_exif(ruta, salida)
        except Exception as exc:
            fallos.append(file_failure(str(ruta), exc))
            logger.warning("Error al limpiar EXIF %s: %s", ruta, exc)
            errores += 1
    return {'fallos': fallos, 'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}
