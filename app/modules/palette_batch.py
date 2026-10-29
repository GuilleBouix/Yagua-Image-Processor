"""Bounded palette cache and sequential batch exports, independent of Tk.

Cache only colors, not full images. Every read checks the source signature;
exports publish atomically without replacing sources or existing files.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from threading import RLock

from app.modules.palette import extraer_paleta, exportar_paleta_imagen


def path_key(path):
    """Canonical identity for duplicate inputs and reserved output paths."""
    import os
    return os.path.normcase(str(Path(path).resolve()))


def file_signature(path):
    """Detect replacements as well as changes to an existing file."""
    stat = Path(path).stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino


class PaletteCache:
    """Serialize extraction and retain at most 500 small palette results."""

    def __init__(self):
        self._lock = RLock()
        self._entries = OrderedDict()

    def clear(self):
        """Release cached colors when the collection is cleared."""
        with self._lock:
            self._entries.clear()

    def extract(self, path, count):
        """Read current colors, rejecting a source that changes mid-read."""
        with self._lock:
            identity, before = path_key(path), file_signature(path)
            key = identity, before, count
            if key in self._entries:
                self._entries.move_to_end(key)
                return self._entries[key]
            palette = tuple(extraer_paleta(path, count))
            if file_signature(path) != before:
                raise OSError('source_changed')
            # Only the latest revision of each file remains useful.
            for old in list(self._entries):
                if old[0] == identity and old[1] != before:
                    del self._entries[old]
            self._entries[key] = palette
            while len(self._entries) > 500:
                self._entries.popitem(last=False)
            return palette


def process_palettes(paths, count, cache, *, folder=None, progress=None):
    """Extract/export each input once, continuing after individual errors.

    progress receives (completed, total). Results retain paths and errors for
    diagnostics while the UI displays only a compact total.
    """
    paths = list(dict.fromkeys(map(path_key, paths)))
    reserved = set(paths)
    results = []
    for index, path in enumerate(paths):
        result = {'path': path, 'output': None, 'palette': (), 'error': ''}
        try:
            palette = cache.extract(path, count)
            result['palette'] = palette
            if folder is not None:
                stem, suffix = Path(path).stem + '_paleta', 0
                while True:
                    name = stem + (f'_{suffix}' if suffix else '') + '.png'
                    target = Path(folder) / name
                    if path_key(target) in reserved or target.exists():
                        suffix += 1
                        continue
                    try:
                        exportar_paleta_imagen(palette, target, replace=False)
                    except FileExistsError:
                        suffix += 1
                        continue
                    reserved.add(path_key(target))
                    result['output'] = str(target)
                    break
        except Exception as error:
            result['error'] = str(error)
        results.append(result)
        if progress is not None:
            progress(index + 1, len(paths))
    return results
