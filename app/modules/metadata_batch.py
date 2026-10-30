"""Sequential metadata operations. No UI objects or translated labels here."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from PIL import Image

from app.modules.metadata import (
    editar_exif, leer_campos_edicion, leer_metadatos, limpiar_exif,
    preparar_campos_exif,
)
from app.utils.output import atomic_write_text, require_single_frame, unique_output_path
from app.utils.saving import get_plan, run_plan, path_key, canonical_format
from app.utils.image_source import mpo_preview_count


@dataclass
class MetadataDraft:
    """Agrupa los valores EXIF editables y las acciones del formulario."""

    values: dict[str, str] = field(default_factory=dict)
    sync_dates: bool = False
    clear_gps: bool = False
    orientation: int | None = None

    @property
    def dirty(self) -> bool:
        """Indica si se cambió algún campo o acción del borrador."""
        return any(self.values.values()) or self.sync_dates or self.clear_gps or self.orientation is not None

    def copy(self) -> MetadataDraft:
        """Crea una copia independiente del borrador actual."""
        return MetadataDraft(dict(self.values), self.sync_dates, self.clear_gps, self.orientation)


@dataclass(frozen=True)
class MetadataTask:
    """Captura la ruta, la versión del archivo y los cambios de una tarea."""

    path: str
    draft: MetadataDraft = field(default_factory=MetadataDraft)
    fingerprint: tuple[int, int] | None = None


def fingerprint(path: str) -> tuple[int, int]:
    """Registra tamaño y fecha de modificación para detectar cambios externos."""
    stat = Path(path).stat()
    return stat.st_size, stat.st_mtime_ns


def leer_archivo(path: str) -> dict:
    """Si la imagen no se puede leer, informa un error en vez de devolver EXIF vacío."""
    before = fingerprint(path)
    with Image.open(path) as image:
        fmt = image.format or ''
        size = image.size
        image.getexif()
        frames = getattr(image, 'n_frames', 1)
        animated = getattr(image, 'is_animated', False)
        camera_preview = bool(mpo_preview_count(image))
    metadata = leer_metadatos(path)
    editable = canonical_format(fmt) in ('JPEG', 'TIFF') and ((frames == 1 and not animated) or camera_preview)
    values, edit_error = {}, None
    if editable:
        try:
            values = leer_campos_edicion(path)
        except Exception as error:
            edit_error = str(error)
    if before != fingerprint(path):
        raise OSError('source_changed')
    return dict(metadata=metadata, values=values, format=fmt, size=size,
                bytes=before[0], fingerprint=before, editable=editable, edit_error=edit_error)


def preparar_borrador(base: dict[str, str], draft: MetadataDraft):
    """Combina cambios explícitos con valores existentes sin borrar campos vacíos."""
    values = {key: value for key, value in draft.values.items() if value and value != base.get(key, '')}
    merged = {**base, **draft.values}
    if draft.sync_dates:
        values['DateTimeOriginal'] = merged.get('DateTimeOriginal', '')
    gps = ('GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection')
    if draft.clear_gps:
        for key in gps:
            values.pop(key, None)
    elif any(key in values for key in gps):
        for key in gps:
            if merged.get(key):
                values[key] = merged[key]
    return preparar_campos_exif(values, sync_dates=draft.sync_dates,
                               clear_gps=draft.clear_gps, orientation=draft.orientation)


def procesar_lote(tasks: tuple[MetadataTask, ...], *, clean: bool = False,
                  overwrite: bool = False, folder: str | None = None, output_policy=None) -> dict:
    """Aplica ediciones por imagen y devuelve fallos parciales sin perder el lote."""
    if output_policy is not None:
        by_path = {path_key(task.path): task for task in tasks}
        def process(source, target):
            """Aplica una tarea con las mismas validaciones de origen y salida que el lote."""
            task = by_path[path_key(source)]
            if task.fingerprint is not None and fingerprint(source) != task.fingerprint:
                raise OSError('source_changed')
            if clean:
                return limpiar_exif(source, target)
            data = leer_archivo(source)
            if not data['editable'] or data['edit_error']:
                raise ValueError(data['edit_error'] or 'meta_read_only')
            request, error = preparar_borrador(data['values'], task.draft)
            if error == 'empty':
                return dict(estado='unchanged')
            if error:
                raise ValueError(error)
            ok, error = editar_exif(source, target, request)
            if not ok:
                raise ValueError(error or 'error_saving')
            return {}
        return run_plan(get_plan(output_policy, tuple(task.path for task in tasks), folder), process)
    if not overwrite and not folder:
        raise ValueError('output_folder_required')
    results = []
    for task in tasks:
        result = dict(ruta=task.path, estado='error', destino='', error='')
        try:
            if task.fingerprint is not None and fingerprint(task.path) != task.fingerprint:
                raise OSError('source_changed')
            require_single_frame(task.path)
            request = None
            if not clean:
                data = leer_archivo(task.path)
                if not data['editable']:
                    result.update(estado='unsupported', error='meta_read_only')
                    results.append(result)
                    continue
                if data['edit_error']:
                    raise ValueError(data['edit_error'])
                request, error = preparar_borrador(data['values'], task.draft)
                if error == 'empty':
                    result['estado'] = 'unchanged'
                    results.append(result)
                    continue
                if error:
                    raise ValueError(error)
            output = Path(task.path) if overwrite else unique_output_path(
                folder or '', task.path, sufijo='_sinexif' if clean else '_exif')[0]
            if clean:
                limpiar_exif(task.path, str(output))
            else:
                ok, error = editar_exif(task.path, str(output), request)
                if not ok:
                    raise ValueError(error or 'error_saving')
            result.update(estado='saved', destino=str(output))
        except Exception as error:
            result['error'] = str(error)
        results.append(result)
    return dict(items=results, ok=sum(r['estado'] == 'saved' for r in results),
                unchanged=sum(r['estado'] == 'unchanged' for r in results),
                errores=sum(r['estado'] in ('error', 'unsupported') for r in results))


def exportar_lote(paths: tuple[str, ...], destination: str, fmt: str) -> list[dict]:
    """Exporta metadatos de varias imágenes a JSON o texto."""
    if fmt not in ('txt', 'json'):
        raise ValueError('invalid_option')
    entries = []
    for path in paths:
        entry = dict(ruta=str(Path(path).resolve()), metadatos={}, error=None)
        try:
            entry['metadatos'] = {
                key: value for key, value in leer_archivo(path)['metadata'].items()
                if not key.startswith('__')
            }
        except Exception as error:
            entry['error'] = str(error)
        entries.append(entry)
    if fmt == 'json':
        text = json.dumps(entries, ensure_ascii=False, indent=2)
    else:
        text = '\n\n'.join('\n'.join([
            entry['ruta'], '=' * 40,
            *[f'{key}: {value}' for key, value in entry['metadatos'].items()],
            *([f"ERROR: {entry['error']}"] if entry['error'] else []),
        ]) for entry in entries)
    atomic_write_text(destination, text)
    return entries
