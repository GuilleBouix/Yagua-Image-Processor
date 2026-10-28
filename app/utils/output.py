"""
Helpers para construir rutas de salida sin sobrescrituras.
Uso compartido por modulos de procesamiento.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import wraps
from inspect import signature
import os
import tempfile
from pathlib import Path
from typing import Tuple


logger = logging.getLogger(__name__)


class DiscardOutput(Exception):
    """El candidato es válido, pero la política de salida indica que no debe publicarse."""
    def __init__(self, result):
        """Guarda el resultado asociado con una salida que no se publicará."""
        self.result = result
        super().__init__('no_improvement')


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
        logger.debug("output: unique_output_path ok (%s)", ruta)
        return ruta, False

    contador = 1
    while True:
        ruta_alt = carpeta / f"{entrada.stem}{sufijo}_{contador}{ext}"
        if not ruta_alt.exists():
            logger.debug("output: unique_output_path conflicto (%s)", ruta_alt)
            return ruta_alt, True
        contador += 1





@contextmanager
def atomic_destination(destination: str | Path, *, replace: bool = True):
    """Publish a complete file on the same filesystem; never expose partial bytes.

    replace=False uses a hard link to publish without a check/overwrite race.
    A filesystem without hard links fails safely rather than replacing a file.
    """
    target = Path(destination)
    fd, name = tempfile.mkstemp(prefix='.yagua-', suffix=target.suffix, dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        yield temporary
        with temporary.open('rb+') as stream:
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, target)
        elif os.name == 'nt':
            os.rename(temporary, target)
        else:
            os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(destination: str | Path, text: str) -> None:
    """Reemplaza un archivo de texto solo después de escribirlo completo."""
    with atomic_destination(destination) as temporary:
        temporary.write_text(text, encoding='utf-8')


def require_single_frame(path: str | Path) -> None:
    """Rechaza entradas animadas o multipágina que no se pueden preservar."""
    from PIL import Image
    with Image.open(path) as image:
        if getattr(image, 'n_frames', 1) != 1 or getattr(image, 'is_animated', False):
            raise ValueError('unsupported_frames')


def safe_image_output(function):
    """Protect path-based processors with the common input/output contract."""
    parameters = signature(function)

    @wraps(function)
    def guarded(*args, **kwargs):
        """Verifica que el origen siga estable antes de publicar la salida temporal."""
        bound = parameters.bind(*args, **kwargs)
        source = Path(bound.arguments['ruta_entrada'])
        destination = Path(bound.arguments['ruta_salida'])
        require_single_frame(source)
        before = source.stat()
        same_file = source.resolve() == destination.resolve()
        try:
            with atomic_destination(destination, replace=same_file) as temporary:
                bound.arguments['ruta_salida'] = str(temporary)
                result = function(*bound.args, **bound.kwargs)
                after = source.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise OSError('source_changed')
        except DiscardOutput as skipped:
            return skipped.result
        if isinstance(result, dict) and 'ruta_salida' in result:
            result['ruta_salida'] = str(destination)
        return result
    return guarded
