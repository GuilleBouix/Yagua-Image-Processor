"""Vectorización de imágenes a SVG usando vtracer.

API pública:
- `vectorizar()`: procesa una imagen
- `batch_vectorizar()`: procesa un lote
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_IMAGENES = 50
MAX_BYTES_PREPROCESO = 1_000_000  # 1 MB
ALLOWED_EXTS = {".png", ".webp", ".tif", ".tiff", ".heic", ".heif"}


def vectorizar(
    ruta_imagen,
    carpeta_salida,
    colormode="color",
    filter_speckle=4,
    color_precision=6,
    layer_difference=16,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=8,
    mode="spline",
):
    """
    Vectoriza una imagen a SVG usando vtracer.

    Parámetros (todos directamente de la API vtracer):
        ruta_imagen      : ruta absoluta a la imagen fuente
        carpeta_salida   : carpeta donde guardar el .svg resultante
        colormode        : 'color' | 'binary'
        filter_speckle   : elimina manchas pequeñas (0-128)
        color_precision  : precisión de paleta de colores (1-8)
        layer_difference : diferencia entre capas de color (0-64)
        corner_threshold : umbral para detectar esquinas en grados (0-180)
        length_threshold : longitud mínima de segmento (0-10.0)
        max_iterations   : iteraciones máximas de optimización (1-20)
        splice_threshold : umbral de empalme de curvas (0-180)
        path_precision   : decimales en paths SVG (1-8)
        mode             : 'spline' | 'polygon' | 'none'

    Retorna dict con:
        ok      : 1 si éxito, 0 si error
        archivo : ruta del .svg generado (o None)
        error   : mensaje de error (o None)
    """
    ext = Path(ruta_imagen).suffix.lower()
    if ext and ext not in ALLOWED_EXTS:
        logger.warning("vectorizar: formato no soportado (%s): %s", ext, ruta_imagen)
        return {"ok": 0, "archivo": None, "error": f"Formato no soportado: {ext}"}

    if not os.path.isfile(ruta_imagen):
        logger.warning(f"Imagen no encontrada: {ruta_imagen}")
        return {"ok": 0, "archivo": None, "error": "Archivo no encontrado"}

    if not os.path.isdir(carpeta_salida):
        logger.warning(f"Carpeta de salida no válida: {carpeta_salida}")
        return {"ok": 0, "archivo": None, "error": "Carpeta de salida no válida"}

    try:
        if os.path.getsize(ruta_imagen) > MAX_BYTES_PREPROCESO:
            logger.warning("vectorizar: denegado (archivo>1MB): %s", ruta_imagen)
            return {"ok": 0, "archivo": None, "error": "Archivo demasiado grande (max 1 MB)"}
    except Exception:
        pass

    try:
        import vtracer

        nombre_base = os.path.splitext(os.path.basename(ruta_imagen))[0]
        ruta_svg = os.path.join(carpeta_salida, f"{nombre_base}.svg")

        # vtracer (Rust) no tolera backslashes en Windows
        ruta_entrada = ruta_imagen.replace("\\", "/")
        ruta_salida  = ruta_svg.replace("\\", "/")

        vtracer.convert_image_to_svg_py(
            ruta_entrada,
            ruta_salida,
            colormode=colormode,
            hierarchical="stacked",
            mode=mode,
            filter_speckle=int(filter_speckle),
            color_precision=int(color_precision),
            layer_difference=int(layer_difference),
            corner_threshold=int(corner_threshold),
            length_threshold=float(length_threshold),
            max_iterations=int(max_iterations),
            splice_threshold=int(splice_threshold),
            path_precision=int(path_precision),
        )

        logger.info(f"SVG generado: {ruta_svg}")
        return {"ok": 1, "archivo": ruta_svg, "error": None}

    except ImportError:
        logger.warning("vtracer no está instalado.")
        return {"ok": 0, "archivo": None, "error": "vtracer no esta instalado"}
    except Exception as e:
        logger.warning(f"Error al vectorizar {ruta_imagen}: {e}")
        return {"ok": 0, "archivo": None, "error": str(e)}


def batch_vectorizar(rutas_imagenes, carpeta_salida, **kwargs):
    """
    Vectoriza m?ltiples im?genes. Acepta los mismos kwargs que vectorizar().

    Retorna dict con:
        ok       : cantidad de im?genes procesadas con ?xito
        errores  : cantidad de errores
        archivos : lista de rutas .svg generados
    """
    archivos_generados = []
    ok = 0
    errores = 0

    for ruta in list(rutas_imagenes)[:MAX_IMAGENES]:
        try:
            res = vectorizar(ruta, carpeta_salida=carpeta_salida, **kwargs)
        except Exception as exc:
            errores += 1
            logger.warning("Error en %s: %s", ruta, exc)
            continue

        if res.get("ok"):
            ok += 1
            archivos_generados.append(res.get("archivo"))
        else:
            errores += 1
            logger.warning("Error en %s: %s", ruta, res.get("error"))

    logger.info(f"Batch vectorizaci?n: {ok} ok, {errores} errores")
    return {"ok": ok, "errores": errores, "archivos": archivos_generados}
