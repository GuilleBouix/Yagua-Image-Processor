"""Bounded, thread-safe cache of reduced pixels; contains no Tk resources."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import os
from pathlib import Path
from threading import RLock
from threading import Thread
from queue import PriorityQueue
from itertools import count

from PIL import Image, ImageOps


@dataclass(frozen=True)
class ReducedImage:
    """Contiene una miniatura reducida y las dimensiones del original."""
    image: Image.Image
    dimensions: tuple[int, int]
    format: str
    bytes: int
    signature: tuple


class ReducedImageCache:
    """Mantiene miniaturas LRU dentro de un presupuesto de memoria."""
    def __init__(self, limit_bytes=64 * 1024 * 1024):
        """Inicializa una caché LRU con el presupuesto máximo de memoria."""
        self.limit_bytes = limit_bytes
        self.bytes = 0
        self._entries: OrderedDict[tuple, ReducedImage] = OrderedDict()
        self._lock = RLock()
        self._generation = 0

    def load(self, path, bounds, *, mode='RGB') -> ReducedImage:
        """Carga o reutiliza una miniatura para el tamaño y modo solicitados."""
        canonical = os.path.normcase(str(Path(path).resolve()))
        stat = Path(canonical).stat()
        signature = (canonical, stat.st_size, stat.st_mtime_ns)
        key = (*signature, tuple(bounds), mode)
        with self._lock:
            cached = self._entries.get(key)
            generation = self._generation
            if cached is not None:
                self._entries.move_to_end(key)
                return cached
        with Image.open(canonical) as source:
            dimensions, format_name = source.size, source.format or ''
            source.draft(mode, bounds)
            image = ImageOps.exif_transpose(source)
            image.thumbnail(bounds, Image.Resampling.LANCZOS)
            image = image.convert(mode)
            image.info.clear()  # Reduced previews must not retain large EXIF/ICC blobs.
        result = ReducedImage(image, dimensions, format_name, stat.st_size, signature)
        final_stat = Path(canonical).stat()
        if (final_stat.st_size, final_stat.st_mtime_ns) != signature[1:]:
            raise OSError('source_changed')
        size = self._cost(image)
        with self._lock:
            if generation != self._generation or size > self.limit_bytes:
                return result
            # Otro lector puede haber agregado la misma imagen mientras tanto.
            if key in self._entries:
                return self._entries[key]
            for stale in [entry for entry in self._entries if entry[0] == canonical and entry[1:3] != signature[1:]]:
                self._remove(stale)
            while self.bytes + size > self.limit_bytes:
                self._remove(next(iter(self._entries)))
            self._entries[key] = result
            self.bytes += size
        return result

    def _remove(self, key):
        """Retira una entrada y descuenta sus bytes estimados."""
        item = self._entries.pop(key)
        self.bytes -= self._cost(item.image)

    @staticmethod
    def _cost(image):
        # Pillow also uses four storage bytes per RGB pixel internally.
        """Calcula el uso aproximado de memoria de una miniatura."""
        return image.width * image.height * max(4, len(image.getbands()))

    def invalidate(self, path=None):
        """Invalida una ruta específica o vacía la caché."""
        canonical = os.path.normcase(str(Path(path).resolve())) if path is not None else None
        with self._lock:
            self._generation += 1
            for key in list(self._entries):
                if canonical is None or key[0] == canonical:
                    self._remove(key)


image_cache = ReducedImageCache()


class ImageRequests:
    """Two bounded-concurrency decoders. Generation checks cancel obsolete work."""
    _queue: PriorityQueue = PriorityQueue()
    _sequence = count()
    _started = False

    def __init__(self, owner):
        """Asocia solicitudes y callbacks con el ciclo de vida de una vista."""
        self.owner = owner
        self.generation = 0
        self.pending: dict[tuple, list] = {}
        if not ImageRequests._started:
            ImageRequests._started = True
            for _ in range(2):
                Thread(target=self._worker, daemon=True, name='yagua-reduced-images').start()

    def cancel(self):
        """Invalida las solicitudes pendientes de esta vista."""
        self.generation += 1
        self.pending.clear()

    def request(self, path, bounds, callback, *, priority=1, mode='RGB'):
        """Solicita una miniatura y entrega el resultado desde el hilo de Tk."""
        key = (str(path), tuple(bounds), mode)
        if key in self.pending:
            self.pending[key].append(callback)
            return
        self.pending[key] = [callback]
        self._queue.put((priority, next(self._sequence), self, self.generation, key))

    @classmethod
    def _worker(cls):
        """Procesa cargas de miniaturas sin crear o modificar widgets."""
        from app.ui.operations import operations
        while True:
            _, _, request, generation, key = cls._queue.get()
            if generation != request.generation:
                continue
            try:
                path, bounds, mode = key
                result, error = image_cache.load(path, bounds, mode=mode), None
            except Exception as exc:
                result, error = None, exc
            if generation != request.generation:
                continue
            def deliver(request=request, generation=generation, key=key, result=result, error=error):
                """Encola la miniatura en la vista solo si su solicitud sigue vigente."""
                if generation == request.generation:
                    for callback in request.pending.pop(key, []):
                        def apply(callback=callback, generation=generation, request=request, result=result, error=error):
                            """Actualiza el widget desde Tk con la imagen reducida recibida."""
                            if generation == request.generation:
                                callback(result, error)
                        operations.post(request.owner, apply)
            operations.post(request.owner, deliver)
            del request, deliver, result, error
