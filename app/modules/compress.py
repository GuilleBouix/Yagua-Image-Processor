"""
Modulo de compresion de imagenes.
Logica pura de procesamiento, sin dependencias de UI.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/compress/services.py: Usa las funciones de este modulo.
    - app/ui/file_list.py: Usa formatear_bytes para mostrar tamanos.
"""

import io
import logging
import shutil
from pathlib import Path

from PIL import Image

from app.modules.image_utils import normalize_common, ensure_rgb_for_jpeg
from app.modules.output import unique_output_path

logger = logging.getLogger(__name__)

# Mapeo de extensiones de archivo a nombres de formato PIL
_EXT_A_FMT = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
    '.avif': 'AVIF',
    '.heic': 'HEIF',
    '.heif': 'HEIF',
    '.ico': 'ICO',
    '.bmp': 'BMP',
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.gif': 'GIF',
}


def _formato_desde_ruta(ruta):
    """
    Obtiene el formato de imagen desde la extension del archivo.
    
    Args:
        ruta: Ruta del archivo de imagen.
        
    Returns:
        Nombre del formato PIL (ej: 'JPEG', 'PNG').
    """
    return _EXT_A_FMT.get(Path(ruta).suffix.lower(), 'JPEG')


def _preparar_imagen(imagen, formato):
    """
    Prepara la imagen para el formato de salida.
    
    Aplica transformaciones necesarias segun el formato destino:
    correccion de rotacion EXIF, conversion de modo de color,
    y manejo de transparencia.
    
    Args:
        imagen: Objeto Image de Pillow.
        formato: Formato de salida (ej: 'JPEG', 'PNG').
        
    Returns:
        Imagen preparada lista para guardar.
    """
    # Corregir rotacion automatica de camaras y moviles usando datos EXIF
    imagen = normalize_common(imagen)

    # Manejo especial para JPEG
    if formato == 'JPEG':
        # JPEG no soporta transparencia, convertir a RGB con fondo blanco
        return ensure_rgb_for_jpeg(imagen)

    # Manejo especial para PNG - reducir a paleta de 256 colores
    if formato == 'PNG':
        # Preserva transparencia via modo P con paleta adaptativa
        return imagen.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)

    # ICO requiere modo RGBA
    if formato == 'ICO':
        return imagen.convert('RGBA')

    return imagen


def _kwargs_guardado(imagen, formato, calidad, quitar_exif):
    """
    Genera los argumentos para el metodo save() segun el formato.
    
    Cada formato tiene sus propios parametros de compresion.
    
    Args:
        imagen: Objeto Image de Pillow.
        formato: Formato de salida.
        calidad: Nivel de calidad (10-100).
        quitar_exif: Si es True, no se incluye metadata EXIF.
        
    Returns:
        Diccionario con argumentos para Image.save().
    """
    # JPEG: calidad, optimizacion y progresivo
    if formato == 'JPEG':
        argumentos_guardado = {'quality': calidad, 'optimize': True, 'progressive': True}
        # Preservar EXIF si esta habilitado y existe
        if not quitar_exif and 'exif' in imagen.info:
            argumentos_guardado['exif'] = imagen.info['exif']
        
        return argumentos_guardado
    
    # WEBP: calidad y metodo de compresion
    if formato == 'WEBP':
        return {'quality': calidad, 'method': 6}
    
    # PNG: optimizacion y nivel de compresion maximo
    if formato == 'PNG':
        return {'optimize': True, 'compress_level': 9}
    
    # AVIF/HEIF: calidad
    if formato in ('AVIF', 'HEIF'):
        return {'quality': calidad}
    
    # ICO: generar multiple tamanos de icono
    if formato == 'ICO':
        max_lado = min(imagen.size)
        sizes = [(s, s) for s in [16, 32, 48, 64, 128, 256] if s <= max_lado]
        
        return {'sizes': sizes or [(max_lado, max_lado)]}
    
    return {}


def comprimir_imagen(ruta_entrada, ruta_salida, calidad=85, quitar_exif=True):
    """
    Comprime una imagen manteniendo su formato original.
    
    Si el archivo comprimido resulta mas grande que el original,
    conserva el archivo original sin cambios.
    
    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Ruta donde guardar la imagen comprimida.
        calidad: Nivel de compresion (10-100). Default 85.
        quitar_exif: Si es True, elimina metadatos EXIF. Default True.
        
    Returns:
        Diccionario con:
            - ruta_salida: Ruta del archivo guardado.
            - tam_original: Tamano original en bytes.
            - tam_comprimido: Tamano comprimido en bytes.
            - reduccion_pct: Porcentaje de reduccion.
            - formato: Formato de la imagen.
    """

    logger.info("Comprimir: %s -> %s (calidad=%s, exif=%s)", ruta_entrada, ruta_salida, calidad, quitar_exif)
    # Determinar formato original
    formato = _formato_desde_ruta(ruta_entrada)
    
    # Guardar tamano original
    tam_original = Path(ruta_entrada).stat().st_size

    # Abrir, preparar y guardar imagen
    with Image.open(ruta_entrada) as imagen:
        imagen = _preparar_imagen(imagen, formato)
        argumentos_guardado = _kwargs_guardado(imagen, formato, calidad, quitar_exif)
        imagen.save(ruta_salida, formato, **argumentos_guardado)

    # Verificar tamano comprimido
    tam_comprimido = Path(ruta_salida).stat().st_size

    # Si el comprimido es mas grande, copiar el original
    if tam_comprimido >= tam_original:
        shutil.copy2(ruta_entrada, ruta_salida)
        tam_comprimido = tam_original

    return {
        'ruta_salida': ruta_salida,
        'tam_original': tam_original,
        'tam_comprimido': tam_comprimido,
        'reduccion_pct': round((1 - tam_comprimido / tam_original) * 100, 1),
        'formato': formato,
    }


def estimar_tamano(ruta_entrada, calidad):
    """
    Estima el tamano resultante de comprimir una imagen.
    
    Usa una version en memoria para no crear archivos temporales.
    
    Args:
        ruta_entrada: Ruta de la imagen a estimar.
        calidad: Nivel de compresion a estimar.
        
    Returns:
        Tamano estimado en bytes.
    """
    # Determinar formato
    formato = _formato_desde_ruta(ruta_entrada)
    
    with Image.open(ruta_entrada) as imagen:
        # Para JPEG, usar draft para reducir procesamiento
        if formato == 'JPEG':
            imagen.draft('RGB', (200, 200))

        # Forzar lectura de datos
        imagen.load()

        # Preparar imagen para el formato
        imagen = _preparar_imagen(imagen, formato)
        
        # Guardar en memoria
        buffer_memoria = io.BytesIO()
        argumentos_guardado = _kwargs_guardado(imagen, formato, calidad, quitar_exif=True)
        imagen.save(buffer_memoria, formato, **argumentos_guardado)
        
        # Retornar tamano del buffer
        return buffer_memoria.tell()


def formatear_bytes(bytes_val):
    """
    Formatea un valor en bytes a una cadena legible.
    
    Args:
        bytes_val: Cantidad de bytes.
        
    Returns:
        Cadena formateada (ej: '1.2 MB', '256 KB').
    """
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val / (1024 * 1024):.2f} MB"


def batch_comprimir(rutas, carpeta_salida, calidad=85, quitar_exif=True, sufijo='_comprimido'):
    """
    Comprime multiples imagenes en lote.
    
    Procesa todas las imagenes y genera estadisticas del batch.
    
    Args:
        rutas: Lista de rutas de imagenes a comprimir.
        carpeta_salida: Carpeta donde guardar las imagenes comprimidas.
        calidad: Nivel de compresion (10-100). Default 85.
        quitar_exif: Si es True, elimina metadatos EXIF. Default True.
        sufijo: Sufijo para agregar al nombre de los archivos. Default '_comprimido'.
        
    Returns:
        Diccionario con:
            - ok: Cantidad de imagenes procesadas correctamente.
            - errores: Cantidad de errores.
            - total_original: Suma de tamanos originales.
            - total_comprimido: Suma de tamanos comprimidos.
            - reduccion_pct: Porcentaje de reduccion total.
            - conflictos: Cantidad de archivos renombrados por colision.
    """

    logger.info("Batch comprimir: %s archivos -> %s", len(rutas), carpeta_salida)
    resultados = []
    errores = 0
    conflictos = 0
    
    # Procesar cada imagen
    for ruta in rutas:
        try:
            salida_path, conflicto = unique_output_path(
                carpeta_salida, ruta, sufijo=sufijo
            )
            salida = str(salida_path)
            if conflicto:
                conflictos += 1
            
            # Comprimir imagen
            res = comprimir_imagen(
                ruta, salida,
                calidad=calidad,
                quitar_exif=quitar_exif
            )
            resultados.append(res)
        except Exception as exc:
            logger.warning("Error al comprimir %s: %s", ruta, exc)
            errores += 1

    # Calcular estadisticas del batch
    total_orig = sum(r['tam_original'] for r in resultados) or 0
    total_comp = sum(r['tam_comprimido'] for r in resultados) or 0
    reduccion = round((1 - total_comp / total_orig) * 100, 1) if total_orig else 0
    
    return {
        'ok': len(resultados),
        'errores': errores,
        'total_original': total_orig,
        'total_comprimido': total_comp,
        'reduccion_pct': reduccion,
        'conflictos': conflictos,
    }
