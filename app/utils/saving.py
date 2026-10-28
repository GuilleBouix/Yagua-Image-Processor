"""Frozen output plans and sequential atomic publication, independent of Tk."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from app.utils.output import atomic_destination, DiscardOutput, require_single_frame
from app.utils.results import file_failure

SaveMode = Literal['copies', 'overwrite']
EXTENSIONS = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff',
              'HEIF': '.heic', 'AVIF': '.avif', 'GIF': '.gif', 'BMP': '.bmp', 'ICO': '.ico'}
ALIASES = {'JPG': 'JPEG', 'HEIC': 'HEIF', 'TIF': 'TIFF'}


def canonical_format(value: str) -> str:
    """Normaliza variantes de nombre al formato reconocido por Pillow."""
    value = value.upper()
    return ALIASES.get(value, value)


def path_key(path):
    """Normaliza una ruta para detectar duplicados entre sistemas."""
    try:
        absolute = str(Path(path).resolve())
    except (OSError, ValueError, RuntimeError):
        # A bad input is reported by its item, rather than aborting the batch.
        absolute = os.path.abspath(str(path))
    return os.path.normcase(absolute)


def fingerprint(path):
    """Obtiene datos de archivo para detectar cambios antes de escribir."""
    stat = Path(path).stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


@dataclass(frozen=True)
class OutputItem:
    """Describe una entrada y el destino asignado por el plan de guardado."""
    source: str
    destination: Path | None
    stamp: tuple | None
    source_format: str = ''
    target_format: str = ''
    replace: bool = False
    error: str = ''


@dataclass(frozen=True)
class OutputPlan:
    """Agrupa los archivos y la política de salida de una operación."""
    mode: SaveMode
    items: tuple[OutputItem, ...]
    protected: frozenset[str]
    inputs: frozenset[str]
    resources: tuple[tuple[str, tuple], ...] = ()

    @property
    def replacements(self):
        """Procesa entradas que reemplazarán su original después de validar."""
        return sum(item.replace and not item.error for item in self.items)

    @property
    def copies(self):
        """Procesa entradas que deben escribirse como copias nuevas."""
        return sum(not item.replace and not item.error for item in self.items)


SavePolicy = SaveMode | OutputPlan


def plan_outputs(paths, folder, mode: SaveMode, target_format=None, *, resources=()):
    """Valida entradas y reserva destinos sin sobrescribir archivos existentes."""
    if mode not in ('copies', 'overwrite'):
        raise ValueError('invalid_option')
    if mode == 'copies' and not folder:
        raise ValueError('output_folder_required')
    unique = {}
    for path in paths:
        unique.setdefault(path_key(path), str(path))
    inputs = frozenset(unique)
    paths = tuple(unique.values())
    protected = frozenset(path_key(path) for path in (*paths, *resources))
    resource_stamps = tuple((str(path), fingerprint(path)) for path in resources)
    resource_keys = {path_key(path) for path in resources}
    items, seen = [], set()
    for value in paths:
        source = Path(value)
        try:
            stamp = fingerprint(source)
            identity = (stamp[0], stamp[1]) if stamp[1] else path_key(source)
            if identity in seen:
                continue
            seen.add(identity)
            require_single_frame(source)
            with Image.open(source) as image:
                original = canonical_format(image.format or '')
            target = canonical_format(target_format or original)
            replace = mode == 'overwrite' and original == target
            if replace and path_key(source) in resource_keys:
                raise ValueError('output_resource_conflict')
            if replace:
                destination = source.resolve()
            else:
                extension = source.suffix if original == target else EXTENSIONS[target]
                directory = Path(folder) if mode == 'copies' else source.parent
                destination = directory / (source.stem + extension)
            items.append(OutputItem(str(source), destination, stamp, original, target, replace))
        except Exception as error:
            items.append(OutputItem(str(source), None, None, error=str(error)))
    return OutputPlan(mode, tuple(items), protected, inputs, resource_stamps)


def get_plan(policy: SavePolicy, paths, folder, target_format=None, *, resources=()):
    """Construye el plan de guardado desde opciones de la interfaz."""
    if isinstance(policy, OutputPlan):
        expected_resources = {path_key(path) for path in resources}
        if expected_resources != {path_key(path) for path, _ in policy.resources} or any(
                not item.error and item.target_format != canonical_format(target_format or item.source_format)
                for item in policy.items):
            raise ValueError('invalid_output_plan')
        if {path_key(path) for path in paths} != policy.inputs:
            raise ValueError('invalid_output_plan')
        return policy
    return plan_outputs(paths, folder, policy, target_format, resources=resources)


def _destination(item, protected):
    """Resuelve la ruta de destino según formato y política de salida."""
    assert item.destination is not None
    if item.replace:
        return item.destination, False
    base = item.destination
    destination, number = base, 0
    while destination.exists() or path_key(destination) in protected:
        number += 1
        destination = base.with_name(f'{base.stem}_{number}{base.suffix}')
    return destination, bool(number)


def run_plan(plan: OutputPlan, processor, *, progress_cb=None) -> dict[str, Any]:
    """Procesa las entradas del plan y registra el resultado por archivo."""
    results, failures = [], []
    for item in plan.items:
        size = item.stamp[2] if item.stamp else 0
        row = dict(ruta=item.source, ruta_entrada=item.source, ruta_salida=None, destino='',
                   estado='error', error='', tam_original=size, tam_resultado=size,
                   tam_comprimido=size, conflicto=False)
        try:
            if item.error:
                raise ValueError(item.error)
            if fingerprint(item.source) != item.stamp:
                raise OSError('source_changed')
            destination, conflict = _destination(item, plan.protected)
            # The outer transaction owns publication; existing processors can
            # safely create their own atomic output at this private stage path.
            with atomic_destination(destination, replace=item.replace) as temporary:
                temporary.unlink()
                values = processor(item.source, str(temporary)) or {}
                if values.get('estado') == 'unchanged':
                    raise DiscardOutput(values)
                if values.get('ok') is False:
                    raise OSError(values.get('error') or 'error_saving')
                with Image.open(temporary) as check:
                    try:
                        check.load()
                        if canonical_format(check.format or '') != item.target_format:
                            raise ValueError('invalid_option')
                    finally:
                        # TIFF can retain a memory map after its file is closed.
                        # Release pixels too before Windows renames the stage.
                        check.close()
                if fingerprint(item.source) != item.stamp or any(
                        fingerprint(path) != stamp for path, stamp in plan.resources):
                    raise OSError('source_changed')
                final_size = temporary.stat().st_size
            row.update(values)
            row.update(estado='saved', ruta_salida=str(destination), destino=str(destination),
                       tam_original=size, tam_resultado=final_size, tam_comprimido=final_size,
                       reemplazado=item.replace, conflicto=conflict)
            if 'salida' in row:
                row['salida'] = str(destination)
        except DiscardOutput as skipped:
            row.update(skipped.result)
            row.update(estado='unchanged', ruta_salida=None, destino='', tam_original=size,
                       tam_resultado=size, tam_comprimido=size)
        except Exception as error:
            row['error'] = str(error)
            failures.append(file_failure(item.source, error))
        results.append(row)
        if progress_cb is not None:
            progress_cb(len(results), len(plan.items))
    total = sum(row['tam_original'] for row in results if row['estado'] != 'error')
    final = sum(row['tam_resultado'] for row in results if row['estado'] != 'error')
    return dict(resultados=results, items=results, fallos=failures,
                ok=sum(row['estado'] == 'saved' for row in results), errores=len(failures),
                sin_mejora=sum(row['estado'] == 'unchanged' for row in results),
                unchanged=sum(row['estado'] == 'unchanged' for row in results),
                conflictos=sum(row['conflicto'] for row in results if row['estado'] == 'saved'),
                total_original=total, total_comprimido=final,
                reduccion_pct=round((1-final/total)*100, 1) if total else 0,
                exif_no_aplicado=sum(row.get('exif_no_aplicado', False) for row in results))
