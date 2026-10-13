"""Preparación de previews y resultados por archivo, sin acceso a Tk."""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from app.modules.lqip import (
    LqipResult,
    batch_procesar,
    exportar_json,
    exportar_txt,
    generar_lqip,
    imagen_a_base64,
)

logger = logging.getLogger(__name__)
PREVIEW_SIZE = (420, 240)


@dataclass(frozen=True)
class SourcePreview:
    index: int
    path: str
    dimensions: tuple[int, int] | None = None
    size: int = 0
    format: str = ''
    image: Image.Image | None = None
    error: str = ''


@dataclass(frozen=True)
class ItemResult:
    index: int
    path: str
    result: LqipResult | None = None
    dimensions: tuple[int, int] | None = None
    jpeg_bytes: int = 0
    uri_bytes: int = 0
    image: Image.Image | None = None
    error: str = ''


def cargar_original(index: int, path: str) -> SourcePreview:
    """Lee metadata real y una imagen pequeña para visualizar el original."""
    try:
        size = Path(path).stat().st_size
        with Image.open(path) as source:
            dimensions = source.size
            format_name = source.format or Path(path).suffix.lstrip('.').upper()
            preview = ImageOps.exif_transpose(source)
            preview.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
            preview = preview.convert('RGBA')
        return SourcePreview(index, path, dimensions, size, format_name, preview)
    except Exception as exc:
        logger.warning('lqip: error en original %s: %s', path, exc)
        return SourcePreview(index, path, error=str(exc))


def procesar_archivos(paths: tuple[str, ...], options: dict) -> list[ItemResult]:
    """Conserva la identidad de cada entrada, incluidos errores y nombres iguales."""
    items = []
    for index, path in enumerate(paths):
        try:
            if options['modo'] == 'lqip':
                result = generar_lqip(path, options['ancho'], options['blur'], options['calidad_lqip'])
            else:
                result = imagen_a_base64(path, options['calidad_b64'])
            jpeg = base64.b64decode(result['base64'], validate=True)
            with Image.open(io.BytesIO(jpeg)) as output:
                dimensions = output.size
                preview = output.copy()
                preview.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
            items.append(ItemResult(
                index, path, result, dimensions, len(jpeg),
                len(result['data_uri'].encode('utf-8')), preview,
            ))
        except Exception as exc:
            logger.warning('lqip: error al generar %s: %s', path, exc)
            items.append(ItemResult(index, path, error=str(exc)))
    return items


__all__ = [
    'batch_procesar', 'exportar_txt', 'exportar_json',
    'cargar_original', 'procesar_archivos', 'SourcePreview', 'ItemResult',
]
