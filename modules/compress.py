"""
Módulo de compresión de imágenes.
Lógica pura de procesamiento, sin dependencias de UI.
"""

import io
import shutil
from pathlib import Path
from PIL import Image, ImageOps


_EXT_A_FMT = {
    '.jpg': 'JPEG', '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
    '.avif': 'AVIF',
    '.ico': 'ICO',
    '.bmp': 'BMP',
    '.tiff': 'TIFF', '.tif': 'TIFF',
    '.gif': 'GIF',
}


def _formato_desde_ruta(ruta: str) -> str:
    return _EXT_A_FMT.get(Path(ruta).suffix.lower(), 'JPEG')


def _preparar_imagen(img: Image.Image, fmt: str) -> Image.Image:
    # Corregir rotación automática de cámaras y móviles
    img = ImageOps.exif_transpose(img)

    # CMYK → RGB (modo impresión no sirve en web/desktop)
    if img.mode == 'CMYK':
        img = img.convert('RGB')

    if fmt == 'JPEG':
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            fondo = Image.new('RGB', img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            return fondo
        return img.convert('RGB')

    if fmt == 'PNG':
        # Reducción a paleta de 256 colores — misma técnica que TinyPNG
        # Preserva transparencia via modo P con info de transparencia
        return img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)

    if fmt == 'ICO':
        return img.convert('RGBA')

    return img


def _kwargs_guardado(img: Image.Image, fmt: str, calidad: int, quitar_exif: bool) -> dict:
    if fmt == 'JPEG':
        kwargs = {'quality': calidad, 'optimize': True, 'progressive': True}
        if not quitar_exif and 'exif' in img.info:
            kwargs['exif'] = img.info['exif']
        return kwargs
    if fmt == 'WEBP':
        return {'quality': calidad, 'method': 6}
    if fmt == 'PNG':
        return {'optimize': True, 'compress_level': 9}
    if fmt == 'AVIF':
        return {'quality': calidad}
    if fmt == 'ICO':
        max_lado = min(img.size)
        sizes = [(s, s) for s in [16, 32, 48, 64, 128, 256] if s <= max_lado]
        return {'sizes': sizes or [(max_lado, max_lado)]}
    return {}


def comprimir_imagen(
    ruta_entrada: str,
    ruta_salida: str,
    calidad: int = 85,
    quitar_exif: bool = True
) -> dict:
    """
    Comprime una imagen manteniendo su formato original.
    Si el resultado pesa más que el original, conserva el original.
    """
    fmt = _formato_desde_ruta(ruta_entrada)
    tam_original = Path(ruta_entrada).stat().st_size

    with Image.open(ruta_entrada) as img:
        img = _preparar_imagen(img, fmt)
        kwargs = _kwargs_guardado(img, fmt, calidad, quitar_exif)
        img.save(ruta_salida, fmt, **kwargs)

    tam_comprimido = Path(ruta_salida).stat().st_size

    if tam_comprimido >= tam_original:
        shutil.copy2(ruta_entrada, ruta_salida)
        tam_comprimido = tam_original

    return {
        'ruta_salida': ruta_salida,
        'tam_original': tam_original,
        'tam_comprimido': tam_comprimido,
        'reduccion_pct': round((1 - tam_comprimido / tam_original) * 100, 1),
        'formato': fmt,
    }


def estimar_tamano(ruta_entrada: str, calidad: int) -> int:
    fmt = _formato_desde_ruta(ruta_entrada)
    with Image.open(ruta_entrada) as img:
        if fmt == 'JPEG':
            img.draft('RGB', (200, 200))

        img.load()  # fuerza lectura del draft — sin reasignar

        img = _preparar_imagen(img, fmt)
        buf = io.BytesIO()
        kwargs = _kwargs_guardado(img, fmt, calidad, quitar_exif=True)
        img.save(buf, fmt, **kwargs)
        return buf.tell()


def formatear_bytes(bytes_val: int) -> str:
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val / (1024 * 1024):.2f} MB"


def batch_comprimir(
    rutas: list[str],
    carpeta_salida: str,
    calidad: int = 85,
    quitar_exif: bool = True,
    sufijo: str = '_comprimido',
) -> dict:
    resultados = []
    errores = 0
    for ruta in rutas:
        try:
            p = Path(ruta)
            salida = str(Path(carpeta_salida) / (p.stem + sufijo + p.suffix))
            res = comprimir_imagen(
                ruta, salida,
                calidad=calidad,
                quitar_exif=quitar_exif
            )
            resultados.append(res)
        except Exception:
            errores += 1

    total_orig = sum(r['tam_original'] for r in resultados) or 0
    total_comp = sum(r['tam_comprimido'] for r in resultados) or 0
    reduccion = round((1 - total_comp / total_orig) * 100, 1) if total_orig else 0
    return {
        'ok': len(resultados),
        'errores': errores,
        'total_original': total_orig,
        'total_comprimido': total_comp,
        'reduccion_pct': reduccion,
    }
