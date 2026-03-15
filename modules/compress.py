"""
Módulo de compresión de imágenes.
Lógica pura de procesamiento, sin dependencias de UI.
"""

import io
from pathlib import Path
from PIL import Image

FORMATOS_SALIDA = ['JPEG', 'WEBP', 'PNG', 'AVIF', 'ICO']

def comprimir_imagen(
    ruta_entrada: str,
    ruta_salida: str,
    calidad: int = 85,
    formato: str = 'WEBP',
    quitar_exif: bool = True
) -> dict:
    """
    Comprime una imagen y la guarda en disco.

    Returns:
        dict con tamaño original, comprimido, porcentaje de reducción y formato.
    """
    img = Image.open(ruta_entrada)
    tam_original = Path(ruta_entrada).stat().st_size
    fmt = formato.upper()

    if fmt == 'JPEG':
        if img.mode in ('RGBA', 'LA', 'P'):
            fondo = Image.new('RGB', img.size, (255, 255, 255))
            
            if img.mode == 'P':
                img = img.convert('RGBA')
            fondo.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = fondo
        else:
            img = img.convert('RGB')
        kwargs = {'quality': calidad, 'optimize': True}
        
        if not quitar_exif and 'exif' in img.info:
            kwargs['exif'] = img.info['exif']
    elif fmt == 'WEBP':
        kwargs = {'quality': calidad, 'method': 6}
    elif fmt == 'PNG':
        kwargs = {'optimize': True}
    elif fmt == 'AVIF':
        kwargs = {'quality': calidad}
    elif fmt == 'ICO':
        # ICO estándar: múltiples resoluciones en un solo archivo
        SIZES_ICO = [16, 32, 48, 64, 128, 256]
        img = img.convert('RGBA')

        # Limita a tamaños que no superen el original
        max_lado = min(img.size)
        sizes = [(s, s) for s in SIZES_ICO if s <= max_lado]
        
        if not sizes:
            sizes = [(max_lado, max_lado)]
        kwargs = {'sizes': sizes}
    else:
        kwargs = {}

    img.save(ruta_salida, fmt, **kwargs)
    tam_comprimido = Path(ruta_salida).stat().st_size

    return {
        'ruta_salida': ruta_salida,
        'tam_original': tam_original,
        'tam_comprimido': tam_comprimido,
        'reduccion_pct': round((1 - tam_comprimido / tam_original) * 100, 1),
        'formato': fmt,
    }


def estimar_tamano(ruta_entrada: str, calidad: int, formato: str = 'WEBP') -> int:
    """
    Estima el tamaño resultante sin guardar en disco.
    Retorna el tamaño estimado en bytes.
    """
    img = Image.open(ruta_entrada)
    fmt = formato.upper()
    buf = io.BytesIO()

    if fmt == 'JPEG':
        img = img.convert('RGB')
        img.save(buf, fmt, quality=calidad, optimize=True)
    elif fmt == 'WEBP':
        img.save(buf, fmt, quality=calidad)
    elif fmt == 'PNG':
        img.save(buf, fmt, optimize=True)
    elif fmt == 'ICO':
        img = img.convert('RGBA')
        img.save(buf, 'ICO', sizes=[(256, 256)])

    else:
        img.save(buf, fmt, quality=calidad)

    return buf.tell()


def formatear_bytes(bytes_val: int) -> str:
    """Convierte bytes a string legible (KB o MB)."""
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    
    return f"{bytes_val / (1024 * 1024):.2f} MB"