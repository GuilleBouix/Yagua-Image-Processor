"""
Modulo de OCR para extraer texto de imagenes.
Usa EasyOCR para reconocimiento de texto.

Relacionado con:
    - app/ui/frames/ocr/: UI relacionada.
"""

import logging
import re
import threading
from pathlib import Path

import cv2
from PIL import features

from app.utils.image_utils import load_cv_image

logger = logging.getLogger(__name__)
_READER_CACHE = {}
_READER_LOCK = threading.Lock()
MAX_IMAGENES = 10


def _idiomas_key(idiomas):
    return tuple([i.strip().lower() for i in idiomas if i and i.strip()])


def get_reader(idiomas):
    """
    Obtiene un reader cacheado para los idiomas solicitados.
    Inicializa en forma lazy si no existe.
    """
    key = _idiomas_key(idiomas)
    with _READER_LOCK:
        if key in _READER_CACHE:
            return _READER_CACHE[key]
        import easyocr
        reader = easyocr.Reader(list(key))
        _READER_CACHE[key] = reader
        return reader


def ensure_reader(idiomas):
    """Fuerza la carga del reader (lazy)."""
    return get_reader(idiomas)


def _avif_supported():
    try:
        return bool(features.check('avif'))
    except Exception:
        return False



def preprocesar_imagen(imagen_path):
    """
    Preprocesa la imagen para mejorar el reconocimiento OCR.

    Args:
        imagen_path: Ruta de la imagen.

    Returns:
        Imagen preprocesada (gris con umbral).
    """
    imagen = load_cv_image(imagen_path)
    if imagen is None:
        raise ValueError("No se pudo abrir la imagen")
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    # Aplicar umbral para mejorar contraste
    _, thresh = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def limpiar_texto(texto):
    """
    Limpia el texto preservando estructura y puntuación.
    Normaliza espacios y caracteres especiales.

    Args:
        texto: Texto (palabra o línea).

    Returns:
        Texto limpio.
    """
    # Preservar puntuación y caracteres españoles
    texto = re.sub(r'[^\w\s.,;:¿?¡!%$@#()\-áéíóúÁÉÍÓÚñÑ/&\'"]+', '', texto)
    # Normalizar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def ordenar_resultados(resultados, tolerancia_y=10):
    """
    Ordena los resultados por filas (agrupa palabras en la misma línea).
    Devuelve una lista de strings donde cada string es una línea de la imagen.

    Args:
        resultados: Lista de resultados de EasyOCR.
        tolerancia_y: Tolerancia en pixels para agrupar en la misma fila.

    Returns:
        Lista de strings ordenados (una por fila).
    """
    if not resultados:
        return []

    # Ordenar por posición Y inicial
    resultados.sort(key=lambda x: x[0][0][1])

    lineas = []
    fila_actual = [resultados[0]]

    for i in range(1, len(resultados)):
        # Si está en la misma fila (dentro de tolerancia Y)
        if resultados[i][0][0][1] <= fila_actual[-1][0][0][1] + tolerancia_y:
            fila_actual.append(resultados[i])
        else:
            # Ordenar la fila terminada por el eje X y unir con espacios
            fila_actual.sort(key=lambda x: x[0][0][0])
            linea_texto = " ".join([r[1] for r in fila_actual])
            lineas.append(linea_texto)
            fila_actual = [resultados[i]]

    # Añadir la última fila
    fila_actual.sort(key=lambda x: x[0][0][0])
    linea_texto = " ".join([r[1] for r in fila_actual])
    lineas.append(linea_texto)

    return lineas


def procesar_imagen(imagen_path, reader):
    """
    Procesa una imagen y extrae el texto usando OCR.

    Args:
        imagen_path: Ruta de la imagen.
        reader: Instancia de EasyOCR Reader.

    Returns:
        Texto extraído concatenado (fiel a la imagen).
    """
    try:
        preprocesada = preprocesar_imagen(imagen_path)
        resultados = reader.readtext(preprocesada)
        # ordenar_resultados devuelve líneas ya formadas (palabras agrupadas)
        lineas = ordenar_resultados(resultados)
        # Limpiar cada línea y unir con saltos de línea
        lineas_limpias = [limpiar_texto(linea) for linea in lineas]
        texto_completo = '\n'.join(lineas_limpias)
        return texto_completo
    except Exception:
        logger.exception("Error procesando imagen %s", imagen_path)
        raise


def batch_procesar(rutas, idiomas=['es', 'en']):
    """
    Procesa un lote de im?genes con OCR.

    Args:
        rutas: Lista de rutas de im?genes.
        idiomas: Lista de idiomas para OCR.

    Returns:
        Diccionario con ok, errores, textos.
    """
    logger.info("batch_procesar: inicio con %d im?genes, idiomas=%s", len(rutas), idiomas)
    avif_omitidos = 0
    if not _avif_supported():
        rutas_filtradas = []
        for ruta in rutas:
            if Path(ruta).suffix.lower() == '.avif':
                avif_omitidos += 1
            else:
                rutas_filtradas.append(ruta)
        rutas = rutas_filtradas
    if not rutas:
        logger.warning("batch_procesar: sin rutas procesables (avif_omitidos=%d)", avif_omitidos)
        return {"ok": 0, "errores": 0, "textos": {}, "avif_omitidos": avif_omitidos}

    reader = get_reader(idiomas)
    textos = {}
    ok = 0
    errores = 0
    for ruta in rutas[:MAX_IMAGENES]:
        try:
            texto = procesar_imagen(ruta, reader)
            textos[str(ruta)] = texto
            ok += 1
            logger.info("Procesada %s: %d caracteres", ruta, len(texto))
        except Exception as e:
            logger.exception("Error procesando %s: %s", ruta, e)
            errores += 1
    logger.info("batch_procesar: fin, ok=%d, errores=%d", ok, errores)
    return {"ok": ok, "errores": errores, "textos": textos, "avif_omitidos": avif_omitidos}


def exportar_texto(texto, carpeta_salida, nombre_base="texto_extraido"):
    """
    Exporta el texto a un archivo .txt.

    Args:
        texto: Texto a exportar.
        carpeta_salida: Carpeta donde guardar.
        nombre_base: Nombre base del archivo.

    Returns:
        Ruta del archivo exportado.
    """
    carpeta = Path(carpeta_salida)
    ruta_final = carpeta / f"{nombre_base}.txt"
    
    # Evitar sobrescrituras
    contador = 1
    while ruta_final.exists():
        ruta_final = carpeta / f"{nombre_base}_{contador}.txt"
        contador += 1
    
    with open(ruta_final, 'w', encoding='utf-8') as f:
        f.write(texto)
    logger.info("Texto exportado a %s", ruta_final)
    return str(ruta_final)
