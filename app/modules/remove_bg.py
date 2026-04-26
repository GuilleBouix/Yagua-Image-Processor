"""
Modulo de eliminacion de fondo de imagenes.
Optimizado para fotos de producto con fondos claros y uniformes.

Relacionado con:
    - app/ui/frames/remove_bg/: UI relacionada.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import logging
import os
from pathlib import Path
import sys
from typing import Callable

import numpy as np
from PIL import Image, ImageOps

from app.utils.output import unique_output_path

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'isnet-general-use'
FALLBACK_MODEL = 'u2netp'
FORMATOS_SALIDA = ['PNG', 'WEBP', 'TIFF']
_FMT_A_EXT = {'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff'}
INSTALL_COMMAND = 'pip install --upgrade rembg onnxruntime pymatting'
MAX_IMAGENES = 10

_SESSION_CACHE: dict[str, object] = {}
_MODEL_READY: set[str] = set()


@dataclass(frozen=True)
class RemoveBgConfig:
    """Configuracion interna del pipeline de remocion de fondo."""

    model_name: str = DEFAULT_MODEL
    post_process_mask: bool = True
    alpha_matting_foreground_threshold: int = 250
    alpha_matting_background_threshold: int = 15
    alpha_matting_erode_size: int = 5


@dataclass(frozen=True)
class BackgroundAnalysis:
    """Resumen del borde de la imagen para decidir refinado."""

    is_light_uniform: bool
    border_ratio: float
    luminance_median: float
    luminance_std: float
    background_rgb: tuple[int, int, int]


def _ensure_stdio():
    """Evita errores de tqdm cuando stdout/stderr no existen (apps GUI)."""
    logger.debug("remove_bg: ensure_stdio")
    if sys.stderr is None:
        sys.stderr = io.StringIO()
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is not None and sys.stdout is not None:
        return
    os.environ.setdefault('TQDM_DISABLE', '1')


def _import_rembg():
    try:
        from rembg import remove as rembg_remove, new_session
    except ImportError:
        raise ImportError(f'rembg no está disponible. Ejecutá: {INSTALL_COMMAND}')
    return rembg_remove, new_session


def _models_dir() -> Path:
    custom_home = os.getenv('U2NET_HOME')
    if custom_home:
        return Path(custom_home).expanduser()

    xdg_data_home = os.getenv('XDG_DATA_HOME')
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / '.u2net'

    return Path.home() / '.u2net'


def _model_path(model_name: str) -> Path:
    return _models_dir() / f'{model_name}.onnx'


def _load_session(model_name: str):
    if model_name in _SESSION_CACHE:
        logger.info("remove_bg: reusar_sesion (modelo=%s)", model_name)
        return _SESSION_CACHE[model_name]

    _, new_session = _import_rembg()
    logger.info("remove_bg: crear_sesion (modelo=%s)", model_name)
    _ensure_stdio()
    session = new_session(model_name)
    _SESSION_CACHE[model_name] = session
    _MODEL_READY.add(model_name)
    return session


def _get_processing_session(model_name: str = DEFAULT_MODEL):
    try:
        session = _load_session(model_name)
        return session, model_name, False
    except Exception:
        if model_name == FALLBACK_MODEL:
            raise

        logger.warning(
            "remove_bg: fallback_compatibilidad (modelo=%s -> %s)",
            model_name,
            FALLBACK_MODEL,
            exc_info=True,
        )
        session = _load_session(FALLBACK_MODEL)
        return session, FALLBACK_MODEL, True


def _extract_border_pixels(rgb: np.ndarray, border_size: int) -> np.ndarray:
    height, width = rgb.shape[:2]
    border = max(1, min(border_size, height, width))
    strips = [
        rgb[:border, :, :].reshape(-1, 3),
        rgb[-border:, :, :].reshape(-1, 3),
    ]

    if height > (border * 2):
        strips.extend(
            [
                rgb[border:-border, :border, :].reshape(-1, 3),
                rgb[border:-border, -border:, :].reshape(-1, 3),
            ]
        )
    else:
        strips.extend(
            [
                rgb[:, :border, :].reshape(-1, 3),
                rgb[:, -border:, :].reshape(-1, 3),
            ]
        )

    return np.concatenate(strips, axis=0)


def _analyze_background(imagen: Image.Image) -> BackgroundAnalysis:
    rgb = np.asarray(imagen.convert('RGB'), dtype=np.float32)
    height, width = rgb.shape[:2]
    border_ratio = 0.05
    border_size = max(1, int(round(min(width, height) * border_ratio)))
    border_pixels = _extract_border_pixels(rgb, border_size)
    luminance = np.dot(border_pixels, np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))
    luminance_median = float(np.median(luminance))
    luminance_std = float(np.std(luminance))
    background_rgb = tuple(
        int(round(channel)) for channel in np.median(border_pixels, axis=0).tolist()
    )
    is_light_uniform = luminance_median >= 235 and luminance_std <= 18

    logger.info(
        "remove_bg: analizar_fondo (uniforme=%s, luminancia_mediana=%.2f, luminancia_std=%.2f, color=%s)",
        is_light_uniform,
        luminance_median,
        luminance_std,
        background_rgb,
    )
    return BackgroundAnalysis(
        is_light_uniform=is_light_uniform,
        border_ratio=border_ratio,
        luminance_median=luminance_median,
        luminance_std=luminance_std,
        background_rgb=background_rgb,
    )


def _to_pil_image(image_like) -> Image.Image:
    if isinstance(image_like, Image.Image):
        return image_like
    return Image.fromarray(image_like)  # type: ignore[arg-type]


def _decontaminate_light_halo(
    imagen: Image.Image,
    background_rgb: tuple[int, int, int],
) -> Image.Image:
    rgba = np.asarray(imagen.convert('RGBA'), dtype=np.float32)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    target = (alpha > 0) & (alpha < 220)
    if not np.any(target):
        return imagen.convert('RGBA')

    bg = np.array(background_rgb, dtype=np.float32).reshape((1, 1, 3))
    distance = np.linalg.norm(rgb - bg, axis=-1)
    near_background = distance <= 60.0
    target &= near_background
    if not np.any(target):
        return imagen.convert('RGBA')

    alpha_factor = np.clip(alpha / 255.0, 0.12, 1.0)
    corrected = (rgb - (bg * (1.0 - alpha_factor[..., None]))) / alpha_factor[..., None]
    corrected = np.clip(corrected, 0.0, 255.0)

    distance_factor = np.clip((60.0 - distance) / 60.0, 0.0, 1.0)
    transparency_factor = np.clip((220.0 - alpha) / 220.0, 0.0, 1.0)
    blend = 0.85 * distance_factor * transparency_factor
    blend = np.where(target, blend, 0.0)[..., None]

    rgb_refined = (rgb * (1.0 - blend)) + (corrected * blend)
    rgba[..., :3] = np.clip(rgb_refined, 0.0, 255.0)
    return Image.fromarray(rgba.astype(np.uint8), mode='RGBA')


def _process_image(
    imagen: Image.Image,
    *,
    rembg_remove,
    session,
    config: RemoveBgConfig,
    status_callback: Callable[[str], None] | None = None,
) -> tuple[Image.Image, BackgroundAnalysis]:
    if status_callback:
        status_callback('analyzing_image')
    analysis = _analyze_background(imagen)

    remove_kwargs = {
        'session': session,
        'post_process_mask': config.post_process_mask,
    }
    if analysis.is_light_uniform:
        remove_kwargs.update(
            {
                'alpha_matting': True,
                'alpha_matting_foreground_threshold': config.alpha_matting_foreground_threshold,
                'alpha_matting_background_threshold': config.alpha_matting_background_threshold,
                'alpha_matting_erode_size': config.alpha_matting_erode_size,
            }
        )

    result = _to_pil_image(rembg_remove(imagen, **remove_kwargs)).convert('RGBA')
    if analysis.is_light_uniform:
        if status_callback:
            status_callback('refining_edges')
        result = _decontaminate_light_halo(result, analysis.background_rgb)
    return result, analysis


def _save_output(
    resultado: Image.Image,
    ruta_base: str,
    ruta_entrada: str,
    *,
    formato_salida: str,
) -> tuple[Path, bool]:
    formato = formato_salida.upper()
    extension = _FMT_A_EXT.get(formato, '.png')
    ruta_final, conflicto = unique_output_path(
        ruta_base,
        ruta_entrada,
        sufijo='_sinFondo',
        extension=extension,
    )
    logger.info("remove_bg: guardar_resultado (ruta=%s, conflicto=%s)", ruta_final, conflicto)
    resultado.save(str(ruta_final), formato)
    return ruta_final, conflicto


def quitar_fondo(ruta_entrada, ruta_salida, formato_salida='PNG'):
    """
    Elimina el fondo de una imagen y exporta con transparencia.

    Args:
        ruta_entrada: Ruta de la imagen original.
        ruta_salida: Carpeta donde guardar el resultado.
        formato_salida: Formato de exportacion (PNG, WEBP, TIFF).

    Returns:
        Diccionario con ruta_salida, tam_original, tam_resultado y metadata del pipeline.
    """
    try:
        rembg_remove, _ = _import_rembg()
        session, model_used, used_fallback = _get_processing_session()
        config = RemoveBgConfig(model_name=model_used)

        logger.info(
            "remove_bg: quitar_fondo inicio (entrada=%s, salida=%s, formato=%s, modelo=%s)",
            ruta_entrada,
            ruta_salida,
            formato_salida,
            model_used,
        )
        _ensure_stdio()
        tam_original = Path(ruta_entrada).stat().st_size

        imagen = Image.open(ruta_entrada)
        imagen = ImageOps.exif_transpose(imagen)
        resultado, analysis = _process_image(
            imagen,
            rembg_remove=rembg_remove,
            session=session,
            config=config,
        )

        ruta_final, conflicto = _save_output(
            resultado,
            ruta_salida,
            ruta_entrada,
            formato_salida=formato_salida,
        )

        return {
            'ruta_salida': str(ruta_final),
            'tam_original': tam_original,
            'tam_resultado': ruta_final.stat().st_size,
            'conflicto': conflicto,
            'model_used': model_used,
            'used_fallback': used_fallback,
            'background_profile': 'light_uniform' if analysis.is_light_uniform else 'general',
        }
    except Exception:
        logger.exception("Error en quitar_fondo para %s", ruta_entrada)
        raise


def batch_quitar_fondo(rutas, carpeta_salida, formato_salida='PNG', status_callback=None):
    """
    Elimina el fondo de multiples imagenes.
    Reutiliza la misma sesion para mayor eficiencia.

    Args:
        rutas: Lista de rutas de imagenes.
        carpeta_salida: Carpeta donde guardar los resultados.
        formato_salida: Formato de exportacion (PNG, WEBP, TIFF).
        status_callback: Callback opcional para reportar estados internos.

    Returns:
        Diccionario con ok, errores, resultados, conflictos y metadata del modelo usado.
    """
    rembg_remove, _ = _import_rembg()
    session, model_used, used_fallback = _get_processing_session()
    config = RemoveBgConfig(model_name=model_used)

    logger.info(
        "remove_bg: batch_inicio (cantidad=%s, carpeta=%s, formato=%s, modelo=%s)",
        len(rutas),
        carpeta_salida,
        formato_salida,
        model_used,
    )
    _ensure_stdio()
    resultados = []
    errores = 0
    conflictos = 0

    for ruta in list(rutas)[:MAX_IMAGENES]:
        try:
            logger.debug("remove_bg: procesar_imagen (ruta=%s)", ruta)
            tam_original = Path(ruta).stat().st_size

            imagen = Image.open(ruta)
            imagen = ImageOps.exif_transpose(imagen)

            resultado, analysis = _process_image(
                imagen,
                rembg_remove=rembg_remove,
                session=session,
                config=config,
                status_callback=status_callback,
            )

            ruta_final, conflicto = _save_output(
                resultado,
                carpeta_salida,
                ruta,
                formato_salida=formato_salida,
            )
            if conflicto:
                conflictos += 1

            resultados.append(
                {
                    'ruta_salida': str(ruta_final),
                    'tam_original': tam_original,
                    'tam_resultado': ruta_final.stat().st_size,
                    'background_profile': 'light_uniform' if analysis.is_light_uniform else 'general',
                }
            )
        except Exception:
            logger.exception("Error al quitar fondo %s", ruta)
            errores += 1

    logger.info(
        "remove_bg: batch_fin (ok=%s, errores=%s, conflictos=%s, modelo=%s, fallback=%s)",
        len(resultados),
        errores,
        conflictos,
        model_used,
        used_fallback,
    )
    return {
        'ok': len(resultados),
        'errores': errores,
        'resultados': resultados,
        'conflictos': conflictos,
        'model_used': model_used,
        'used_fallback': used_fallback,
    }


def ensure_model(model_name: str = DEFAULT_MODEL, allow_fallback: bool = True):
    """
    Fuerza la descarga/carga del modelo si no existe aun.

    Returns:
        Diccionario con el modelo finalmente cargado.
    """
    if model_name in _MODEL_READY:
        logger.info("remove_bg: ensure_model (ya_listo=True, modelo=%s)", model_name)
        return {'model_used': model_name, 'used_fallback': False}

    logger.info("remove_bg: ensure_model (descargar_si_falta, modelo=%s)", model_name)
    if allow_fallback:
        _, model_used, used_fallback = _get_processing_session(model_name)
    else:
        _load_session(model_name)
        model_used = model_name
        used_fallback = False

    logger.info("remove_bg: ensure_model listo (modelo=%s, fallback=%s)", model_used, used_fallback)
    return {'model_used': model_used, 'used_fallback': used_fallback}


def estado_rembg():
    """Verifica si rembg puede importarse y retorna detalle del error si falla."""
    try:
        import rembg  # noqa: F401
        return True, None
    except Exception as exc:
        detalle = str(exc).strip() or type(exc).__name__
        logger.warning("rembg no disponible: %s", detalle)
        return False, detalle


def rembg_disponible():
    """Verifica si rembg esta disponible en el entorno actual."""
    disponible, _ = estado_rembg()
    return disponible


def modelo_descargado(model_name: str = DEFAULT_MODEL):
    """Verifica si el modelo indicado ya fue descargado."""
    if model_name in _MODEL_READY:
        logger.debug("remove_bg: modelo_descargado (cache=True, modelo=%s)", model_name)
        return True

    ruta_modelo = _model_path(model_name)
    ok = ruta_modelo.exists()
    logger.debug(
        "remove_bg: modelo_descargado (modelo=%s, archivo=%s, ok=%s)",
        model_name,
        ruta_modelo,
        ok,
    )
    return ok
