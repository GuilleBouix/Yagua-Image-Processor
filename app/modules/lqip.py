"""
Modulo de generacion de LQIP y Base64.
Convierte imagenes a base64 con distintos formatos de salida.

Relacionado con:
    - app/ui/frames/lqip/: UI relacionada.
"""

import base64
import io
import json
import logging
from pathlib import Path

from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

def imagen_a_base64(ruta, calidad=85):
    """
    Convierte una imagen completa a string base64.

    Args:
        ruta: Ruta de la imagen.
        calidad: Calidad de compresion JPEG (1-100).

    Returns:
        Diccionario con base64, data_uri, html_tag, css_bg.
    """
    imagen = Image.open(ruta)
    buffer = io.BytesIO()

    if imagen.mode in ('RGBA', 'LA', 'P'):
        imagen = imagen.convert('RGB')

    imagen.save(buffer, format='JPEG', quality=calidad, optimize=True)
    datos = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return _construir_resultado(datos, Path(ruta).name)


def generar_lqip(ruta, ancho=20, blur=2.0, calidad=40):
    """
    Genera un Low Quality Image Placeholder (LQIP).
    Imagen minima y borrosa lista para usar como placeholder.

    Args:
        ruta: Ruta de la imagen original.
        ancho: Ancho del placeholder en pixeles.
        blur: Radio de desenfoque gaussiano.
        calidad: Calidad de compresion JPEG (1-100).

    Returns:
        Diccionario con base64, data_uri, html_tag, css_bg, bytes.
    """
    imagen = Image.open(ruta)

    if imagen.mode in ('RGBA', 'LA', 'P'):
        imagen = imagen.convert('RGB')

    # Calcular alto proporcional
    ratio = imagen.height / imagen.width
    alto = max(1, int(ancho * ratio))

    # Reducir y desenfocar
    thumbnail = imagen.resize((ancho, alto), Image.Resampling.LANCZOS)
    thumbnail = thumbnail.filter(ImageFilter.GaussianBlur(radius=blur))

    buffer = io.BytesIO()
    thumbnail.save(buffer, format='JPEG', quality=calidad, optimize=True)
    datos = base64.b64encode(buffer.getvalue()).decode('utf-8')

    resultado = _construir_resultado(datos, Path(ruta).name)
    resultado['bytes'] = len(buffer.getvalue())
    resultado['dimensiones'] = f'{ancho}x{alto}px'

    return resultado


def _construir_resultado(datos_b64, nombre_archivo):
    """
    Construye el diccionario de resultados con todos los formatos.

    Args:
        datos_b64: String base64 de la imagen.
        nombre_archivo: Nombre del archivo original.

    Returns:
        Diccionario con data_uri, html_tag, css_bg.
    """
    data_uri = f'data:image/jpeg;base64,{datos_b64}'
    nombre_css = Path(nombre_archivo).stem.replace(' ', '-').lower()

    return {
        'nombre': nombre_archivo,
        'base64': datos_b64,
        'data_uri': data_uri,
        'html_tag': f'<img src="{data_uri}" alt="{Path(nombre_archivo).stem}" />',
        'css_bg': f'.{nombre_css} {{\n  background-image: url("{data_uri}");\n}}',
    }


def batch_procesar(rutas, modo='lqip', ancho=20, blur=2.0, calidad_lqip=40, calidad_b64=85):
    """
    Procesa multiples imagenes en lote.

    Args:
        rutas: Lista de rutas de imagenes.
        modo: 'lqip' o 'base64'.
        ancho: Ancho del LQIP en pixeles.
        blur: Radio de desenfoque para LQIP.
        calidad_lqip: Calidad JPEG para LQIP.
        calidad_b64: Calidad JPEG para base64 completo.

    Returns:
        Diccionario con resultados, ok, errores.
    """
    resultados = []
    errores = 0

    for ruta in rutas:
        try:
            if modo == 'lqip':
                res = generar_lqip(ruta, ancho=ancho, blur=blur, calidad=calidad_lqip)
            else:
                res = imagen_a_base64(ruta, calidad=calidad_b64)
            resultados.append(res)
        except Exception as exc:
            logger.warning("Error al procesar LQIP %s: %s", ruta, exc)
            errores += 1

    return {
        'resultados': resultados,
        'ok': len(resultados),
        'errores': errores,
    }


def exportar_txt(resultados, ruta_salida, campo='data_uri'):
    """
    Exporta los resultados a archivo .txt.

    Args:
        resultados: Lista de diccionarios de resultados.
        ruta_salida: Ruta del archivo de salida.
        campo: Campo a exportar ('data_uri', 'html_tag', 'css_bg').
    """
    lineas = []
    for res in resultados:
        lineas.append(f'/* {res["nombre"]} */')
        lineas.append(res.get(campo, ''))
        lineas.append('')

    Path(ruta_salida).write_text('\n'.join(lineas), encoding='utf-8')


def exportar_json(resultados, ruta_salida):
    """
    Exporta todos los campos de cada resultado a .json.

    Args:
        resultados: Lista de diccionarios de resultados.
        ruta_salida: Ruta del archivo de salida.
    """
    datos = [
        {
            'nombre':   r['nombre'],
            'data_uri': r['data_uri'],
            'html_tag': r['html_tag'],
            'css_bg':   r['css_bg'],
        }
        for r in resultados
    ]
    Path(ruta_salida).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
