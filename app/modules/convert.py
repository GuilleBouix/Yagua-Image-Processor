"""
Modulo de conversion de imagenes.
Convierte entre formatos manteniendo la mejor calidad posible.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/convert/services.py: Usa las funciones de este modulo.
"""

from pathlib import Path

from PIL import Image, ImageOps


# Lista de formatos de destino disponibles
FORMATOS_DESTINO = ['JPEG', 'PNG', 'WEBP', 'AVIF', 'ICO', 'BMP', 'TIFF', 'GIF']

# Mapeo de formato a extension de archivo
_FMT_A_EXT = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'WEBP': '.webp',
    'AVIF': '.avif',
    'ICO': '.ico',
    'BMP': '.bmp',
    'TIFF': '.tiff',
    'GIF': '.gif',
}

# Mapeo de extension a formato
_EXT_A_FMT = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
    '.avif': 'AVIF',
    '.ico': 'ICO',
    '.bmp': 'BMP',
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.gif': 'GIF',
}


def _preparar_para(imagen, fmt_destino):
    """
    Convierte el modo de la imagen segun lo que acepta el formato destino.
    
    Aplica las transformaciones necesarias para que la imagen
    sea compatible con el formato de salida.
    
    Args:
        imagen: Objeto Image de Pillow.
        fmt_destino: Formato de destino (ej: 'JPEG', 'PNG').
        
    Returns:
        Imagen convertida al modo apropiado.
    """
    # Corregir rotacion de camara usando datos EXIF
    imagen = ImageOps.exif_transpose(imagen)

    # Convertir CMYK a RGB siempre (modo impresion no compatible)
    if imagen.mode == 'CMYK':
        imagen = imagen.convert('RGB')

    # JPEG no soporta transparencia - usar fondo blanco
    if fmt_destino == 'JPEG':
        if imagen.mode in ('RGBA', 'LA', 'P'):
            if imagen.mode == 'P':
                imagen = imagen.convert('RGBA')
            fondo = Image.new('RGB', imagen.size, (255, 255, 255))
            fondo.paste(imagen, mask=imagen.split()[-1] if imagen.mode == 'RGBA' else None)
            return fondo
        return imagen.convert('RGB')

    # PNG soporta todo - normalizar solo si tiene paleta
    if fmt_destino == 'PNG':
        if imagen.mode == 'P':
            return imagen.convert('RGBA')
        return imagen

    # WEBP soporta RGBA
    if fmt_destino == 'WEBP':
        if imagen.mode not in ('RGB', 'RGBA'):
            return imagen.convert('RGBA')
        return imagen

    # GIF solo soporta paleta de 256 colores
    if fmt_destino == 'GIF':
        return imagen.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)

    # ICO requiere RGBA
    if fmt_destino == 'ICO':
        return imagen.convert('RGBA')

    # BMP y TIFF soportan RGB, RGBA y escala de grises
    if fmt_destino in ('BMP', 'TIFF'):
        if imagen.mode not in ('RGB', 'RGBA', 'L'):
            return imagen.convert('RGB')
        return imagen

    # AVIF soporta RGB y RGBA
    if fmt_destino == 'AVIF':
        if imagen.mode not in ('RGB', 'RGBA'):
            return imagen.convert('RGB')
        return imagen

    return imagen


def _kwargs_para(formato, calidad):
    """
    Genera los argumentos para guardar segun el formato.
    
    Args:
        formato: Formato de salida.
        calidad: Nivel de calidad (10-100).
        
    Returns:
        Diccionario con argumentos para Image.save().
    """
    # JPEG con optimizacion progresiva
    if formato == 'JPEG':
        return {'quality': calidad, 'optimize': True, 'progressive': True}
    
    # WEBP con metodo de compresion optimizado
    if formato == 'WEBP':
        return {'quality': calidad, 'method': 6}
    
    # PNG con maxima compresion
    if formato == 'PNG':
        return {'optimize': True, 'compress_level': 9}
    
    # AVIF con calidad
    if formato == 'AVIF':
        return {'quality': calidad}
    
    # ICO con multiples tamanos
    if formato == 'ICO':
        return {'sizes': [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]}
    
    # GIF con optimizacion
    if formato == 'GIF':
        return {'optimize': True}
    
    return {}


def formato_soporta_calidad(formato):
    """
    Verifica si un formato soporta parametro de calidad.
    
    Args:
        formato: Formato a verificar.
        
    Returns:
        True si el formato soporta calidad, False si no.
    """
    return formato.upper() not in {'PNG', 'ICO', 'BMP', 'GIF'}


def convertir_imagen(ruta_entrada, fmt_destino, carpeta_salida, calidad=90):
    """
    Convierte una imagen al formato destino.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        fmt_destino: Formato de destino (ej: 'JPEG', 'PNG').
        carpeta_salida: Carpeta donde guardar la imagen convertida.
        calidad: Nivel de calidad (10-100). Default 90.
        
    Returns:
        Diccionario con:
            - ruta_entrada: Ruta original.
            - ruta_salida: Ruta del archivo convertido.
            - fmt_origen: Formato original.
            - fmt_destino: Formato de destino.
            - tam_original: Tamano original en bytes.
            - tam_resultado: Tamano convertido en bytes.
    """
    formato = fmt_destino.upper()
    
    # Validar formato
    if formato not in _FMT_A_EXT:
        raise ValueError(f'Formato destino no soportado: {formato}')
    
    # Obtener extension del formato
    extension = _FMT_A_EXT[formato]
    
    ruta_archivo = Path(ruta_entrada)
    
    # Construir ruta de salida
    ruta_salida = str(Path(carpeta_salida) / (ruta_archivo.stem + extension))

    # Abrir y convertir imagen
    with Image.open(ruta_entrada) as imagen:
        fmt_origen = _EXT_A_FMT.get(ruta_archivo.suffix.lower(), 'JPEG')

        imagen = _preparar_para(imagen, formato)
        argumentos_guardado = _kwargs_para(formato, calidad)
        imagen.save(ruta_salida, formato, **argumentos_guardado)

    return {
        'ruta_entrada': ruta_entrada,
        'ruta_salida': ruta_salida,
        'fmt_origen': fmt_origen,
        'fmt_destino': formato,
        'tam_original': ruta_archivo.stat().st_size,
        'tam_resultado': Path(ruta_salida).stat().st_size,
    }


def batch_convertir(rutas, fmt_destino, carpeta_salida, calidad=90, progress_cb=None):
    """
    Convierte multiples imagenes al formato destino.
    
    Args:
        rutas: Lista de rutas de imagenes a convertir.
        fmt_destino: Formato de destino.
        carpeta_salida: Carpeta donde guardar las imagenes.
        calidad: Nivel de calidad. Default 90.
        progress_cb: Callback para reportar progreso (actual, total).
        
    Returns:
        Lista de diccionarios con resultados individuales.
    """
    resultados = []
    
    for i, ruta in enumerate(rutas):
        res = convertir_imagen(ruta, fmt_destino, carpeta_salida, calidad)
        resultados.append(res)
        
        # Reportar progreso si hay callback
        if progress_cb:
            progress_cb(i + 1, len(rutas))
    
    return resultados


def batch_convertir_safe(rutas, fmt_destino, carpeta_salida, calidad=90):
    """
    Convierte multiples imagenes con manejo de errores.
    
    Args:
        rutas: Lista de rutas de imagenes a convertir.
        fmt_destino: Formato de destino.
        carpeta_salida: Carpeta donde guardar las imagenes.
        calidad: Nivel de calidad. Default 90.
        
    Returns:
        Diccionario con:
            - ok: Cantidad de conversiones exitosas.
            - errores: Cantidad de errores.
            - fmt_destino: Formato de destino.
    """
    resultados = []
    errores = 0
    
    for ruta in rutas:
        try:
            res = convertir_imagen(ruta, fmt_destino, carpeta_salida, calidad)
            resultados.append(res)
        except Exception:
            errores += 1
    
    return {
        'ok': len(resultados),
        'errores': errores,
        'fmt_destino': fmt_destino.upper(),
    }
