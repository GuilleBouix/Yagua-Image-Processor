"""
Modulo de eliminacion de fondo de imagenes.
Usa el modelo u2netp (liviano ~4MB) via rembg.

Relacionado con:
    - app/ui/frames/remove_bg/: UI relacionada.
"""

import logging
import io
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps

from app.modules.output import unique_output_path

logger = logging.getLogger(__name__)

MODELO = 'u2netp'
FORMATOS_SALIDA = ['PNG', 'WEBP', 'TIFF']
_FMT_A_EXT = {'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff'}
_MODEL_READY = False


def _ensure_stdio():
    """Evita errores de tqdm cuando stdout/stderr no existen (apps GUI)."""
    logger.debug("remove_bg: ensure_stdio")
    if sys.stderr is None:
        sys.stderr = io.StringIO()
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is not None and sys.stdout is not None:
        return
    # Fallback extra si el runtime reemplaza streams luego
    os.environ.setdefault('TQDM_DISABLE', '1')


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
        try:
            from rembg import remove as rembg_remove, new_session
        except ImportError:
            raise ImportError('rembg no est? instalado. Ejecut?: pip install rembg')

        logger.info(
            "remove_bg: quitar_fondo inicio (entrada=%s, salida=%s, formato=%s)",
            ruta_entrada, ruta_salida, formato_salida
        )
        _ensure_stdio()
        imagen = Image.open(ruta_entrada)
        imagen = ImageOps.exif_transpose(imagen)
        tam_original = Path(ruta_entrada).stat().st_size

        logger.info("remove_bg: crear_sesion (modelo=%s)", MODELO)
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
        logger.info(
            "remove_bg: guardar_resultado (ruta=%s, conflicto=%s)",
            ruta_final, conflicto
        )
        resultado.save(str(ruta_final), formato)

        return {
            'ruta_salida': str(ruta_final),
            'tam_original': tam_original,
            'tam_resultado': ruta_final.stat().st_size,
            'conflicto': conflicto,
        }
    except Exception:
        logger.exception("Error en quitar_fondo para %s", ruta_entrada)
        raise


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

    logger.info(
        "remove_bg: batch_inicio (cantidad=%s, carpeta=%s, formato=%s)",
        len(rutas), carpeta_salida, formato_salida
    )
    _ensure_stdio()
    logger.info("remove_bg: crear_sesion (modelo=%s)", MODELO)
    sesion = new_session(MODELO)
    formato = formato_salida.upper()
    extension = _FMT_A_EXT.get(formato, '.png')
    resultados = []
    errores = 0
    conflictos = 0

    for ruta in rutas:
        try:
            logger.debug("remove_bg: procesar_imagen (ruta=%s)", ruta)
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
            logger.debug(
                "remove_bg: guardar_resultado (ruta=%s, conflicto=%s)",
                ruta_final, conflicto
            )
            resultado.save(str(ruta_final), formato)

            resultados.append({
                'ruta_salida': str(ruta_final),
                'tam_original': tam_original,
                'tam_resultado': ruta_final.stat().st_size,
            })
        except Exception as exc:
            logger.exception("Error al quitar fondo %s", ruta)
            errores += 1

    logger.info(
        "remove_bg: batch_fin (ok=%s, errores=%s, conflictos=%s)",
        len(resultados), errores, conflictos
    )
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
    global _MODEL_READY
    if _MODEL_READY:
        logger.info("remove_bg: ensure_model (ya_listo=True)")
        return
    try:
        from rembg import new_session
    except ImportError:
        raise ImportError('rembg no est? instalado.')

    logger.info("remove_bg: ensure_model (descargar_si_falta, modelo=%s)", MODELO)
    _ensure_stdio()
    new_session(MODELO)
    _MODEL_READY = True
    logger.info("remove_bg: ensure_model listo")


def rembg_disponible():
    """Verifica si rembg esta instalado."""
    try:
        import rembg  # noqa: F401
        logger.debug("remove_bg: rembg_disponible=True")
        return True
    except Exception as exc:
        logger.warning("rembg no disponible: %s", exc)
        return False


def modelo_descargado():
    """Verifica si el modelo u2netp ya fue descargado."""
    if _MODEL_READY:
        logger.debug("remove_bg: modelo_descargado (cache=True)")
        return True
    ruta_modelo = Path.home() / '.u2net' / f'{MODELO}.onnx'
    ok = ruta_modelo.exists()
    logger.debug("remove_bg: modelo_descargado (archivo=%s, ok=%s)", ruta_modelo, ok)
    return ok
