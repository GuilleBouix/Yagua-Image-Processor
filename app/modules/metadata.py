"""
Modulo de metadatos EXIF.
Ver, editar, limpiar y exportar metadatos de imagenes.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/metadata/services.py: Usa las funciones de este modulo.
"""

import json
import logging
from pathlib import Path

from PIL import Image, ImageOps
import piexif

from app.modules.output import unique_output_path

logger = logging.getLogger(__name__)


# Campos EXIF legibles con etiquetas amigables
_CAMPOS_LEGIBLES = {
    'Make':             'Camara (marca)',
    'Model':            'Camara (modelo)',
    'LensModel':        'Lente',
    'DateTime':         'Fecha y hora',
    'DateTimeOriginal': 'Fecha original',
    'ISO':              'ISO',
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
}

# Campos editables por el usuario
CAMPOS_EDITABLES = {
    'Artist':    'Autor',
    'Copyright': 'Copyright',
    'Software':  'Software',
    'DateTime':  'Fecha y hora',
}


def _fraccion_a_float(val):
    """
    Convierte una fraccion (numerador, denominador) a float.
    
    Args:
        val: Tupla (numerador, denominador) o numero directo.
        
    Returns:
        Valor como float.
    """
    if isinstance(val, tuple) and len(val) == 2:
        numerator, denominator = val
        if isinstance(numerator, (int, float)) and isinstance(denominator, (int, float)) and denominator != 0:
            return float(numerator) / float(denominator)
        
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    return 0.0


def _formatear_valor(nombre_tag, val):
    """
    Convierte valores EXIF a strings legibles.
    
    Formatea valores especiales como fracciones, coordenadas
    GPS y otros tipos de datos EXIF.
    
    Args:
        nombre_tag: Nombre del tag EXIF.
        val: Valor a formatear.
        
    Returns:
        Cadena legible con el valor formateado.
    """
    # Decodificar bytes como UTF-8
    if isinstance(val, bytes):
        try:
            return val.decode('utf-8').strip('\x00')
        except Exception:
            return val.hex()

    # Formatear numero f/ para apertura
    if nombre_tag == 'FNumber':
        return f'f/{_fraccion_a_float(val):.1f}'

    # Formatear tiempo de exposicion
    if nombre_tag == 'ExposureTime':
        f = _fraccion_a_float(val)
        if f < 1:
            return f'1/{int(round(1/f))}s'
        return f'{f:.1f}s'

    # Formatear distancia focal
    if nombre_tag == 'FocalLength':
        return f'{_fraccion_a_float(val):.0f}mm'

    # Formatear coordenadas GPS
    if nombre_tag in ('GPSLatitude', 'GPSLongitude'):
        if isinstance(val, (list, tuple)) and len(val) == 3:
            grados = _fraccion_a_float(val[0])
            minutos = _fraccion_a_float(val[1])
            segundos = _fraccion_a_float(val[2])
            return f'{grados:.0f}° {minutos:.0f}\' {segundos:.2f}"'

    # Formatear tuplas genericas
    if isinstance(val, tuple):
        return str(val[0]) if len(val) == 2 and val[1] == 1 else str(val)

    return str(val)


def leer_metadatos(ruta):
    """
    Lee los metadatos EXIF de una imagen.
    
    Args:
        ruta: Ruta de la imagen.
        
    Returns:
        Diccionario con etiqueta legible como clave y valor formateado.
        Incluye clave especial '__gps_decimal__' para coordenadas GPS.
    """

    logger.info("Leer metadatos: %s", ruta)
    resultado = {}

    try:
        # Abrir imagen y obtener datos EXIF
        with Image.open(ruta) as img:
            info = img.getexif()
        if not info:
            return resultado

        # Obtener mapa de tags numericos a nombres
        from PIL.ExifTags import TAGS
        tags_num = {nombre: tag_id for tag_id, nombre in TAGS.items()}

        # Extraer cada campo definido
        for nombre, etiqueta in _CAMPOS_LEGIBLES.items():
            num = tags_num.get(nombre)
            if num and num in info:
                val = info[num]
                resultado[etiqueta] = _formatear_valor(nombre, val)

        # Extraer coordenadas GPS para Google Maps
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
    if referencia_gps in ('S', 'W'):
        decimal = -decimal
    
    return round(decimal, 6)


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
        imagen = ImageOps.exif_transpose(imagen)
        tam_original = Path(ruta_entrada).stat().st_size

        formato = imagen.format or 'JPEG'
        
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


def editar_exif(ruta_entrada, ruta_salida, campos):
    """
    Edita campos EXIF especificos y guarda la imagen.
    
    Solo soporta JPEG y TIFF que tienen soporte EXIF real.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen editada.
        campos: Diccionario con nombre_campo como clave y nuevo_valor.
        
    Returns:
        Tupla (ok, warning). Si ok es True pero warning no es None, la
        imagen se guardo sin EXIF por formato no compatible.
    """

    logger.info("Editar EXIF: %s -> %s", ruta_entrada, ruta_salida)
    try:
        with Image.open(ruta_entrada) as imagen:
            formato = imagen.format or 'JPEG'

            # Solo JPEG y TIFF soportan EXIF editable
            if formato not in ('JPEG', 'TIFF'):
                imagen.save(ruta_salida, formato)
                return True, 'no_exif'

            try:
                exif_dict = piexif.load(ruta_entrada)
            except Exception:
                # Crear estructura EXIF vacia si falla la lectura
                exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}}

            # Mapa de campos a tags de piexif
            _PIEXIF_MAP = {
                'Artist':    (piexif.ImageIFD.Artist,    '0th'),
                'Copyright': (piexif.ImageIFD.Copyright, '0th'),
                'Software':  (piexif.ImageIFD.Software,  '0th'),
                'DateTime':  (piexif.ImageIFD.DateTime,  '0th'),
            }

            # Aplicar cada campo
            for campo, valor in campos.items():
                if campo in _PIEXIF_MAP:
                    nombre_tag, ifd = _PIEXIF_MAP[campo]
                    exif_dict[ifd][nombre_tag] = valor.encode('utf-8')

            # Guardar con EXIF modificado
            exif_bytes = piexif.dump(exif_dict)
            imagen.save(ruta_salida, formato, exif=exif_bytes, quality=95)
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
    Path(ruta).write_text(''.join(lineas), encoding='utf-8')


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
    Path(ruta).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


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


def preparar_campos_exif(campos_edit):
    """
    Prepara los campos editados para guardar.
    
    Filtra campos vacios y valida que haya algo que guardar.
    
    Args:
        campos_edit: Diccionario con campos a editar.
        
    Returns:
        Tupla (campos_filtrados, error). Si error es None, exito.
    """
    campos = {
        clave: valor
        for clave, valor in campos_edit.items()
        if valor.strip()
    }
    if not campos:
        return {}, 'empty'
    return campos, None


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
            logger.warning("Error al limpiar EXIF %s: %s", ruta, exc)
            errores += 1
    return {'ok': len(rutas) - errores, 'errores': errores, 'conflictos': conflictos}
