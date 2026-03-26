"""
Modulo de eliminacion de fondo de imagenes.
Usa el modelo u2netp (liviano ~4MB) via rembg.

Relacionado con:
    - app/ui/frames/remove_bg/: UI relacionada.
"""

import logging
from pathlib import Path

from PIL import Image, ImageOps

from app.modules.output import unique_output_path

logger = logging.getLogger(__name__)

MODELO = 'u2netp'
FORMATOS_SALIDA = ['PNG', 'WEBP', 'TIFF']
_FMT_A_EXT = {'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff'}


def quitar_fondo(ruta_entrada, ruta_salida, formato_salida='PNG'):
    """
    Elimina el fondo de una imagen y exporta con transparencia.

    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Carpeta donde guardar el resultado.
        formato_salida: Formato de exportacion (PNG, WEBP, TIFF).

    Returns:
        Diccionario con ruta_salida, tam_original, tam_resultado.
    """
    try:
        from rembg import remove as rembg_remove, new_session
    except ImportError:
        raise ImportError('rembg no está instalado. Ejecutá: pip install rembg')

    imagen = Image.open(ruta_entrada)
    imagen = ImageOps.exif_transpose(imagen)
    tam_original = Path(ruta_entrada).stat().st_size

    sesion = new_session(MODELO)
    resultado_raw = rembg_remove(imagen, session=sesion)
    if isinstance(resultado_raw, Image.Image):
        resultado = resultado_raw
    else:
        resultado = Image.fromarray(resultado_raw)  # type: ignore

    formato = formato_salida.upper()
    extension = _FMT_A_EXT.get(formato, '.png')

    ruta_final, conflicto = unique_output_path(
        ruta_salida, ruta_entrada, sufijo='_sinFondo', extension=extension
    )
    resultado.save(str(ruta_final), formato)

    return {
        'ruta_salida': str(ruta_final),
        'tam_original': tam_original,
        'tam_resultado': ruta_final.stat().st_size,
        'conflicto': conflicto,
    }


def batch_quitar_fondo(rutas, carpeta_salida, formato_salida='PNG'):
    """
    Elimina el fondo de multiples imagenes.
    Reutiliza la misma sesion para mayor eficiencia.

    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar los resultados.
        formato_salida: Formato de exportacion (PNG, WEBP, TIFF).

    Returns:
        Diccionario con ok, errores, resultados y conflictos.
    """
    try:
        from rembg import remove as rembg_remove, new_session
    except ImportError:
        raise ImportError('rembg no está instalado.')

    sesion = new_session(MODELO)
    formato = formato_salida.upper()
    extension = _FMT_A_EXT.get(formato, '.png')
    resultados = []
    errores = 0
    conflictos = 0

    for ruta in rutas:
        try:
            imagen = Image.open(ruta)
            imagen = ImageOps.exif_transpose(imagen)
            tam_original = Path(ruta).stat().st_size

            resultado_raw = rembg_remove(imagen, session=sesion)
            if isinstance(resultado_raw, Image.Image):
                resultado = resultado_raw
            else:
                resultado = Image.fromarray(resultado_raw)  # type: ignore

            ruta_final, conflicto = unique_output_path(
                carpeta_salida, ruta, sufijo='_sinFondo', extension=extension
            )
            if conflicto:
                conflictos += 1
            resultado.save(str(ruta_final), formato)

            resultados.append({
                'ruta_salida': str(ruta_final),
                'tam_original': tam_original,
                'tam_resultado': ruta_final.stat().st_size,
            })
        except Exception as exc:
            logger.warning("Error al quitar fondo %s: %s", ruta, exc)
            errores += 1

    return {
        'ok': len(resultados),
        'errores': errores,
        'resultados': resultados,
        'conflictos': conflictos,
    }


def ensure_model():
    """
    Fuerza la descarga/carga del modelo si no existe aun.

    Usa new_session(MODELO) para que rembg gestione la descarga.
    """
    try:
        from rembg import new_session
    except ImportError:
        raise ImportError('rembg no está instalado.')

    new_session(MODELO)


def rembg_disponible():
    """Verifica si rembg esta instalado."""
    try:
        import rembg  # noqa: F401
        return True
    except Exception as exc:
        logger.warning("rembg no disponible: %s", exc)
        return False


def modelo_descargado():
    """Verifica si el modelo u2netp ya fue descargado."""
    ruta_modelo = Path.home() / '.u2net' / f'{MODELO}.onnx'
    return ruta_modelo.exists()
