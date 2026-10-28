"""Coordinación global de trabajos largos de la interfaz."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Any
from queue import SimpleQueue
from threading import Thread
from threading import Lock
from uuid import uuid4
from time import perf_counter


@dataclass(frozen=True)
class Operation:
    """Identifica un trabajo global y la vista que lo inició."""
    id: str
    owner: object
    label: str


class OperationCoordinator:
    """Permite un solo trabajo global y protege sus transiciones de estado."""

    def __init__(self) -> None:
        """Inicializa el bloqueo y las colas de resultados y llamadas de interfaz."""
        self._deliveries: SimpleQueue[tuple[object, Callable[[], Any]]] = SimpleQueue()
        self._lock = Lock()
        self._active: Operation | None = None
        self._completions: SimpleQueue[
            tuple[Operation, Any, BaseException | None, Callable[[Any], Any], Callable[[BaseException], None]]
        ] = SimpleQueue()

    @property
    def active(self) -> Operation | None:
        """Devuelve el trabajo activo como dato inmutable."""
        with self._lock:
            return self._active

    def begin(self, owner: object, label: str) -> Operation | None:
        """Reserva el coordinador si no hay otro trabajo en curso."""
        with self._lock:
            if self._active is not None:
                return None
            operation = Operation(uuid4().hex, owner, label)
            self._active = operation
            return operation

    def finish(self, operation_id: str) -> bool:
        """Libera el trabajo solo si su identificador sigue activo."""
        with self._lock:
            if self._active is None or self._active.id != operation_id:
                return False
            self._active = None
            return True

    def is_busy(self, owner: object | None = None) -> bool:
        """Comprueba si hay un trabajo global o uno del módulo indicado."""
        with self._lock:
            return self._active is not None and (owner is None or self._active.owner is owner)

    def submit(
        self,
        owner: object,
        label: str,
        work: Callable[[], Any],
        on_success: Callable[[Any], Any],
        on_error: Callable[[BaseException], None],
    ) -> bool:
        """Inicia el worker y encola la respuesta para procesarla desde Tk."""
        operation = self.begin(owner, label)
        if operation is None:
            return False

        def run() -> None:
            """Ejecuta una tarea y devuelve su resultado o propaga el fallo capturado."""
            try:
                self._completions.put((operation, work(), None, on_success, on_error))
            except BaseException as error:
                self._completions.put((operation, None, error, on_success, on_error))

        try:
            Thread(target=run, daemon=True).start()
        except Exception as error:
            self.finish(operation.id)
            on_error(error)
            return False
        return True

    def drain(self, widget_exists=lambda owner: True) -> None:
        """Entrega resultados vigentes en Tk e ignora callbacks obsoletos."""
        deadline = perf_counter() + .008
        while not self._completions.empty():
            operation, result, error, on_success, on_error = self._completions.get()
            current = self.active
            if current is None or current.id != operation.id:
                continue
            self.finish(operation.id)
            try:
                if widget_exists(operation.owner):
                    (on_error if error else on_success)(error if error else result)
            except Exception:
                logging.getLogger(__name__).exception('Operation result delivery failed')
            finally:
                self.finish(operation.id)

        while not self._deliveries.empty():
            if perf_counter() >= deadline:
                break
            owner, callback = self._deliveries.get()
            try:
                if widget_exists(owner):
                    callback()
            except Exception:
                logging.getLogger(__name__).exception('UI delivery failed')

    def post(self, owner: object, callback: Callable[[], Any]) -> None:
        """Thread-safe delivery; never calls Tk from a worker."""
        self._deliveries.put((owner, callback))


operations = OperationCoordinator()
