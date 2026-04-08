"""
Módulo de marca de agua (watermark) para imágenes.

Aplica una imagen watermark sobre imágenes base con control
de posición, tamaño relativo, opacidad y margen.

Relacionado con:
    - app/ui/frames/watermark/services.py: Re-exporta estas funciones.
"""

import logging
import os

import cv2
import numpy as np

from app.utils.image_utils import load_cv_image_unchanged

logger = logging.getLogger(__name__)

POSICIONES = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]


def _cargar_rgba(ruta):
    """Carga una imagen y garantiza que tenga 4 canales (BGRA)."""
    img = load_cv_image_unchanged(ruta)
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


def _calcular_posicion(base_h, base_w, wm_h, wm_w, posicion, margen_px):
    """Calcula coordenadas (x, y) del watermark según posición y margen."""
    m = margen_px
    if posicion == "top-left":
        return m, m
    elif posicion == "top-right":
        return base_w - wm_w - m, m
    elif posicion == "bottom-left":
        return m, base_h - wm_h - m
    elif posicion == "bottom-right":
        return base_w - wm_w - m, base_h - wm_h - m
    else:  # center
        return (base_w - wm_w) // 2, (base_h - wm_h) // 2


def _componer(base_bgra, wm_bgra, x, y, opacidad):
    """
    Superpone wm_bgra sobre base_bgra en (x, y) con alpha blending.
    Modifica una copia de base_bgra y la retorna.
    """
    resultado = base_bgra.copy()
    h_base, w_base = base_bgra.shape[:2]
    h_wm,   w_wm   = wm_bgra.shape[:2]

    # Recortar si el watermark se sale de la imagen
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_base, x + w_wm)
    y2 = min(h_base, y + h_wm)

    if x2 <= x1 or y2 <= y1:
        return resultado  # no hay área de superposición

    # Región del watermark que cae dentro de la imagen
    wm_x1 = x1 - x
    wm_y1 = y1 - y
    wm_x2 = wm_x1 + (x2 - x1)
    wm_y2 = wm_y1 + (y2 - y1)

    roi_base = resultado[y1:y2, x1:x2].astype(np.float32)
    roi_wm   = wm_bgra[wm_y1:wm_y2, wm_x1:wm_x2].astype(np.float32)

    # Alpha combinado: alpha_wm * opacidad_global
    alpha_base = roi_base[:, :, 3:4] / 255.0
    alpha_wm   = (roi_wm[:, :, 3:4] / 255.0) * opacidad

    out_alpha = alpha_wm + alpha_base * (1.0 - alpha_wm)
    # Evitar division por cero
    out_alpha_safe = np.where(out_alpha > 0, out_alpha, 1.0)

    out_rgb = (
        roi_wm[:, :, :3] * alpha_wm
        + roi_base[:, :, :3] * alpha_base * (1.0 - alpha_wm)
    ) / out_alpha_safe

    roi_base[:, :, :3] = out_rgb
    roi_base[:, :, 3:4] = out_alpha * 255.0
    resultado[y1:y2, x1:x2] = np.clip(roi_base, 0, 255).astype(np.uint8)

    return resultado


def aplicar_watermark(
    ruta_imagen,
    ruta_watermark,
    ruta_salida,
    posicion="bottom-right",
    escala=0.25,
    opacidad=0.6,
    margen=20,
):
    """
    Aplica un watermark a una imagen y guarda el resultado.

    Parámetros:
        ruta_imagen    : imagen base
        ruta_watermark : imagen del watermark (admite PNG con alpha)
        ruta_salida    : destino del archivo resultante
        posicion       : 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center'
        escala         : tamaño del watermark como fracción del ancho base (0.05-1.0)
        opacidad       : opacidad del watermark (0.0-1.0)
        margen         : margen en píxeles desde el borde

    Retorna dict:
        ok     : True | False
        salida : ruta del archivo generado
        error  : mensaje de error (o None)
    """
    base = _cargar_rgba(ruta_imagen)
    if base is None:
        return {"ok": False, "salida": None, "error": "No se pudo cargar la imagen base"}

    wm = _cargar_rgba(ruta_watermark)
    if wm is None:
        return {"ok": False, "salida": None, "error": "No se pudo cargar el watermark"}

    h_base, w_base = base.shape[:2]

    # Redimensionar watermark según escala relativa al ancho base
    nuevo_ancho = max(1, int(w_base * escala))
    # Limitar para que no supere la imagen
    nuevo_ancho = min(nuevo_ancho, w_base, h_base)
    ratio       = nuevo_ancho / wm.shape[1]
    nuevo_alto  = max(1, int(wm.shape[0] * ratio))
    nuevo_alto  = min(nuevo_alto, h_base)

    wm_resized = cv2.resize(wm, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_AREA)

    x, y = _calcular_posicion(h_base, w_base, nuevo_alto, nuevo_ancho, posicion, margen)

    resultado = _componer(base, wm_resized, x, y, opacidad)

    cv2.imwrite(ruta_salida, resultado)
    logger.info(f"Watermark aplicado: {ruta_salida}")
    return {"ok": True, "salida": ruta_salida, "error": None}


def aplicar_watermark_np(base_bgra, wm_bgra, posicion="bottom-right", escala=0.25, opacidad=0.6, margen=20):
    """
    Versión in-memory para preview. Opera sobre arrays numpy BGRA.
    Retorna array BGRA resultante o None si falla.
    """
    try:
        h_base, w_base = base_bgra.shape[:2]
        nuevo_ancho = max(1, min(int(w_base * escala), w_base, h_base))
        ratio       = nuevo_ancho / wm_bgra.shape[1]
        nuevo_alto  = max(1, min(int(wm_bgra.shape[0] * ratio), h_base))
        wm_resized  = cv2.resize(wm_bgra, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_AREA)
        x, y = _calcular_posicion(h_base, w_base, nuevo_alto, nuevo_ancho, posicion, margen)
        return _componer(base_bgra, wm_resized, x, y, opacidad)
    except Exception as e:
        logger.warning(f"Error en preview watermark: {e}")
        return None


def batch_aplicar_watermark(rutas_imagenes, ruta_watermark, carpeta_salida, sufijo="_wm", **kwargs):
    """
    Aplica watermark a múltiples imágenes.

    Retorna dict:
        ok       : cantidad procesadas con éxito
        errores  : cantidad de errores
        archivos : lista de rutas generadas
    """
    ok = 0
    errores = 0
    archivos = []

    for ruta in rutas_imagenes:
        nombre_base = os.path.splitext(os.path.basename(ruta))[0]
        ext         = os.path.splitext(ruta)[1] or ".png"
        nombre_out  = f"{nombre_base}{sufijo}{ext}"
        ruta_salida = os.path.join(carpeta_salida, nombre_out)

        res = aplicar_watermark(ruta, ruta_watermark, ruta_salida, **kwargs)

        if res["ok"]:
            ok += 1
            archivos.append(res["salida"])
        else:
            errores += 1
            logger.warning(f"Error en {ruta}: {res['error']}")

    logger.info(f"Batch watermark: {ok} ok, {errores} errores")
    return {"ok": ok, "errores": errores, "archivos": archivos}
