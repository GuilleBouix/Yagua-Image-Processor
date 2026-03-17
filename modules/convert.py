"""
Módulo de conversión de imágenes.
Convierte entre formatos manteniendo la mejor calidad posible.
"""

from pathlib import Path
from PIL import Image, ImageOps


FORMATOS_DESTINO = ['JPEG', 'PNG', 'WEBP', 'AVIF', 'ICO', 'BMP', 'TIFF', 'GIF']

_FMT_A_EXT = {
    'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp',
    'AVIF': '.avif', 'ICO': '.ico', 'BMP': '.bmp',
    'TIFF': '.tiff', 'GIF': '.gif',
}

_EXT_A_FMT = {
    '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG',
    '.webp': 'WEBP', '.avif': 'AVIF', '.ico': 'ICO',
    '.bmp': 'BMP', '.tiff': 'TIFF', '.tif': 'TIFF', '.gif': 'GIF',
}


def _preparar_para(img: Image.Image, fmt_destino: str) -> Image.Image:
    """Convierte el modo de la imagen según lo que acepta el formato destino."""

    # Corregir rotación de cámara
    img = ImageOps.exif_transpose(img)

    # CMYK → RGB siempre
    if img.mode == 'CMYK':
        img = img.convert('RGB')

    if fmt_destino == 'JPEG':
        # JPEG no soporta transparencia — fondo blanco
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            fondo = Image.new('RGB', img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            return fondo
        return img.convert('RGB')

    if fmt_destino == 'PNG':
        # PNG soporta todo — solo normalizar P con transparencia
        if img.mode == 'P':
            return img.convert('RGBA')
        return img

    if fmt_destino == 'WEBP':
        # WEBP soporta RGBA
        if img.mode not in ('RGB', 'RGBA'):
            return img.convert('RGBA')
        return img

    if fmt_destino == 'GIF':
        # GIF solo soporta paleta
        return img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)

    if fmt_destino == 'ICO':
        return img.convert('RGBA')

    if fmt_destino in ('BMP', 'TIFF'):
        if img.mode not in ('RGB', 'RGBA', 'L'):
            return img.convert('RGB')
        return img

    if fmt_destino == 'AVIF':
        if img.mode not in ('RGB', 'RGBA'):
            return img.convert('RGB')
        return img

    return img


def _kwargs_para(fmt: str, calidad: int) -> dict:
    if fmt == 'JPEG':
        return {'quality': calidad, 'optimize': True, 'progressive': True}
    if fmt == 'WEBP':
        return {'quality': calidad, 'method': 6}
    if fmt == 'PNG':
        return {'optimize': True, 'compress_level': 9}
    if fmt == 'AVIF':
        return {'quality': calidad}
    if fmt == 'ICO':
        return {'sizes': [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]}
    if fmt == 'GIF':
        return {'optimize': True}
    return {}


def formato_soporta_calidad(fmt: str) -> bool:
    return fmt.upper() not in {'PNG', 'ICO', 'BMP', 'GIF'}


def convertir_imagen(
    ruta_entrada: str,
    fmt_destino: str,
    carpeta_salida: str,
    calidad: int = 90,
) -> dict:
    """
    Convierte una imagen al formato destino.
    Returns dict con rutas, formatos y tamaños.
    """
    fmt = fmt_destino.upper()
    if fmt not in _FMT_A_EXT:
        raise ValueError(f'Formato destino no soportado: {fmt}')
    ext = _FMT_A_EXT[fmt]
    p = Path(ruta_entrada)
    ruta_salida = str(Path(carpeta_salida) / (p.stem + ext))

    with Image.open(ruta_entrada) as img:
        fmt_origen = _EXT_A_FMT.get(p.suffix.lower(), 'JPEG')

        img = _preparar_para(img, fmt)
        kwargs = _kwargs_para(fmt, calidad)
        img.save(ruta_salida, fmt, **kwargs)

    return {
        'ruta_entrada': ruta_entrada,
        'ruta_salida': ruta_salida,
        'fmt_origen': fmt_origen,
        'fmt_destino': fmt,
        'tam_original': p.stat().st_size,
        'tam_resultado': Path(ruta_salida).stat().st_size,
    }


def batch_convertir(
    rutas: list[str],
    fmt_destino: str,
    carpeta_salida: str,
    calidad: int = 90,
    progress_cb=None
) -> list[dict]:
    resultados = []
    for i, ruta in enumerate(rutas):
        res = convertir_imagen(ruta, fmt_destino, carpeta_salida, calidad)
        resultados.append(res)
        if progress_cb:
            progress_cb(i + 1, len(rutas))
    return resultados


def batch_convertir_safe(
    rutas: list[str],
    fmt_destino: str,
    carpeta_salida: str,
    calidad: int = 90,
) -> dict:
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
