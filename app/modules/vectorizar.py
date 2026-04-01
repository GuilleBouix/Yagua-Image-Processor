"""
Módulo de vectorización de imágenes a SVG usando vtracer.

Expone dos niveles de API:
  - vectorizar()       : imagen individual, parámetros internos directos
  - batch_vectorizar() : múltiples imágenes, mismos parámetros

Los parámetros internos son los de vtracer; la traducción
desde los sliders de la UI ocurre en frame.py.

Relacionado con:
    - app/ui/frames/vectorizar/services.py: Re-exporta estas funciones.
"""

import logging
import os
import io
import tempfile

logger = logging.getLogger(__name__)


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
    if not os.path.isfile(ruta_imagen):
        logger.warning(f"Imagen no encontrada: {ruta_imagen}")
        return {"ok": 0, "archivo": None, "error": "Archivo no encontrado"}

    if not os.path.isdir(carpeta_salida):
        logger.warning(f"Carpeta de salida no válida: {carpeta_salida}")
        return {"ok": 0, "archivo": None, "error": "Carpeta de salida no válida"}

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
        raise
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

    for ruta in rutas_imagenes:
        res = vectorizar(ruta, carpeta_salida=carpeta_salida, **kwargs)
        if res["ok"]:
            ok += 1
            archivos_generados.append(res["archivo"])
        else:
            errores += 1
            logger.warning(f"Error en {ruta}: {res['error']}")

    logger.info(f"Batch vectorizaci?n: {ok} ok, {errores} errores")
    return {"ok": ok, "errores": errores, "archivos": archivos_generados}
