"""
Helpers para construir rutas de salida sin sobrescrituras.
Uso compartido por modulos de procesamiento.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


def unique_output_path(
    carpeta_salida: str | Path,
    ruta_entrada: str | Path,
    *,
    sufijo: str = '',
    extension: str | None = None,
) -> Tuple[Path, bool]:
    """
    Construye una ruta de salida unica para evitar sobrescrituras.

    Args:
        carpeta_salida: Carpeta donde guardar el archivo.
        ruta_entrada: Ruta del archivo original.
        sufijo: Sufijo a agregar al nombre base.
        extension: Extension de salida (incluyendo el punto). Si es None,
            usa la extension de ruta_entrada.

    Returns:
        (ruta_salida, conflicto) donde conflicto indica que se renombro
        para evitar sobrescritura.
    """
    carpeta = Path(carpeta_salida)
    entrada = Path(ruta_entrada)
    ext = extension or entrada.suffix
    if ext and not ext.startswith('.'):
        ext = f'.{ext}'

    base = f"{entrada.stem}{sufijo}{ext}"
    ruta = carpeta / base
    if not ruta.exists():
        return ruta, False

    contador = 1
    while True:
        ruta_alt = carpeta / f"{entrada.stem}{sufijo}_{contador}{ext}"
        if not ruta_alt.exists():
            return ruta_alt, True
        contador += 1
