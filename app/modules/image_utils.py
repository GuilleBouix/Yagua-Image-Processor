"""
Helpers comunes de preparacion de imagenes.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageOps


logger = logging.getLogger(__name__)


def init_heif_support() -> bool:
    """
    Registra el soporte HEIF/HEIC en Pillow si la dependencia existe.
    """
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        logger.info("image_utils: HEIF opener registrado")
        return True
    except Exception:
        logger.info("image_utils: HEIF opener no disponible")
        return False


def heif_supported() -> bool:
    """
    Indica si el soporte HEIF/HEIC esta disponible en el runtime.
    """
    try:
        import pillow_heif
        return True
    except Exception:
        return False


def load_cv_image(ruta) -> "object | None":
    """
    Carga una imagen en formato BGR compatible con OpenCV.
    Soporta rutas con acentos usando imdecode.
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        return None

    try:
        data = np.fromfile(str(ruta), dtype=np.uint8)
        if data.size:
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is not None:
                logger.debug("image_utils: load_cv_image imdecode ok (%s)", ruta)
                return img
    except Exception:
        pass

    try:
        img_pil = Image.open(ruta)
        img_pil = ImageOps.exif_transpose(img_pil).convert('RGB')
        arr = np.array(img_pil)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def load_cv_image_unchanged(ruta) -> "object | None":
    """
    Carga una imagen preservando canales (incluye alpha si existe).
    Soporta rutas con acentos usando imdecode.
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        return None

    try:
        data = np.fromfile(str(ruta), dtype=np.uint8)
        if data.size:
            img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
            if img is not None:
                logger.debug("image_utils: load_cv_image_unchanged imdecode ok (%s)", ruta)
                return img
    except Exception:
        pass

    try:
        img_pil = Image.open(ruta)
        img_pil = ImageOps.exif_transpose(img_pil)
        if img_pil.mode in ("RGBA", "LA"):
            img_pil = img_pil.convert("RGBA")
            arr = np.array(img_pil)
            return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        img_pil = img_pil.convert("RGB")
        arr = np.array(img_pil)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def normalize_common(imagen: Image.Image) -> Image.Image:
    """
    Normaliza la imagen con operaciones comunes:
    - Corrige orientacion EXIF
    - Convierte CMYK a RGB
    """
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode == 'CMYK':
        imagen = imagen.convert('RGB')
    return imagen


def ensure_rgb_for_jpeg(imagen: Image.Image) -> Image.Image:
    """
    Convierte una imagen a RGB apto para JPEG, manejando transparencia.
    """
    if imagen.mode in ('RGBA', 'LA', 'P'):
        if imagen.mode == 'P':
            imagen = imagen.convert('RGBA')
        fondo = Image.new('RGB', imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.split()[-1] if imagen.mode == 'RGBA' else None)
        return fondo
    return imagen.convert('RGB')


def save_cv_image(ruta, imagen) -> bool:
    """
    Guarda un array de OpenCV en disco de forma segura (Windows-friendly).
    """
    try:
        import cv2
    except Exception:
        return False

    try:
        ext = Path(ruta).suffix or ".png"
        ok, buf = cv2.imencode(ext, imagen)
        if not ok:
            return False
        buf.tofile(str(ruta))
        logger.debug("image_utils: save_cv_image ok (%s)", ruta)
        return True
    except Exception:
        return False
