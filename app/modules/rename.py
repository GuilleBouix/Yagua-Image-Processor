"""
Modulo de renombrado de archivos en lote.
Aplica transformaciones en cadena sobre los nombres de archivo.

Relacionado con:
    - app/ui/frames/rename/: UI relacionada.
"""

from datetime import datetime
from pathlib import Path


def generar_nombres_preview(rutas, opciones):
    """
    Genera preview de nuevos nombres sin modificar archivos.

    Args:
        rutas: Lista de rutas de archivos.
        opciones: Diccionario con opciones de renombrado.

    Returns:
        Lista de tuplas (nombre_original, nombre_nuevo).
    """
    resultado = []
    for indice, ruta in enumerate(rutas):
        ruta_archivo = Path(ruta)
        nombre_original = ruta_archivo.stem
        extension = ruta_archivo.suffix
        nombre_nuevo = _aplicar_transformaciones(nombre_original, indice, opciones)
        resultado.append((ruta_archivo.name, nombre_nuevo + extension))
    return resultado


def _aplicar_transformaciones(nombre, indice, opciones):
    """
    Aplica transformaciones en este orden:
    1. Capitalización (sobre el nombre original)
    2. Numeración con prefijo (reemplaza o agrega número)
    3. Fecha (siempre envuelve el resultado final)
    """
    try:
        inicio = int(opciones.get('inicio', 1))
    except (ValueError, TypeError):
        inicio = 1

    nombre_resultado = nombre

    # Paso 1 — Prefijo + numeración
    if opciones.get('numeracion_activa'):
        prefijo = opciones.get('prefijo', '').strip()
        numero = str(indice + inicio).zfill(3)
        if prefijo:
            nombre_resultado = f'{prefijo}_{numero}'
        else:
            nombre_resultado = f'{nombre_resultado}_{numero}'

    # Paso 2 — Fecha
    if opciones.get('fecha_activa'):
        formato = opciones.get('formato_fecha', '%Y%m%d')
        try:
            fecha = datetime.now().strftime(formato)
        except Exception:
            fecha = datetime.now().strftime('%Y%m%d')

        if opciones.get('posicion_fecha') == 'sufijo':
            nombre_resultado = f'{nombre_resultado}_{fecha}'
        else:
            nombre_resultado = f'{fecha}_{nombre_resultado}'

    # Paso 3 — Capitalización al final sobre todo el resultado
    caso = opciones.get('caso', 'sin_cambio')
    if caso == 'minusculas':
        nombre_resultado = nombre_resultado.lower()
    elif caso == 'mayusculas':
        nombre_resultado = nombre_resultado.upper()

    return nombre_resultado


def renombrar_archivos(rutas, opciones):
    """
    Renombra los archivos originales en su ubicacion actual.

    Args:
        rutas: Lista de rutas de archivos.
        opciones: Diccionario con opciones de renombrado.

    Returns:
        Diccionario con ok, errores, conflictos.
    """
    ok = 0
    errores = 0
    conflictos = 0

    for indice, ruta in enumerate(rutas):
        try:
            ruta_archivo = Path(ruta)
            nombre_original = ruta_archivo.stem
            extension = ruta_archivo.suffix
            nombre_nuevo = _aplicar_transformaciones(nombre_original, indice, opciones)

            if nombre_nuevo == nombre_original:
                ok += 1
                continue

            ruta_nueva = ruta_archivo.parent / (nombre_nuevo + extension)

            if ruta_nueva.exists() and ruta_nueva != ruta_archivo:
                conflictos += 1
                continue

            ruta_archivo.rename(ruta_nueva)
            ok += 1

        except Exception:
            errores += 1

    return {
        'ok': ok,
        'errores': errores,
        'conflictos': conflictos,
    }