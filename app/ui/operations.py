"""Coordinación global de trabajos largos de la interfaz."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any
from queue import SimpleQueue
from threading import Thread
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class Operation:
    id: str
    owner: object
    label: str


class OperationCoordinator:
    """Permite un solo trabajo global y protege sus transiciones de estado."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._active: Operation | None = None
        self._completions: SimpleQueue[
            tuple[Operation, Any, BaseException | None, Callable[[Any], None], Callable[[BaseException], None]]
        ] = SimpleQueue()

    @property
    def active(self) -> Operation | None:
        with self._lock:
            return self._active

    def begin(self, owner: object, label: str) -> Operation | None:
        with self._lock:
            if self._active is not None:
                return None
            operation = Operation(uuid4().hex, owner, label)
            self._active = operation
            return operation

    def finish(self, operation_id: str) -> bool:
        with self._lock:
            if self._active is None or self._active.id != operation_id:
                return False
            self._active = None
            return True

    def is_busy(self, owner: object | None = None) -> bool:
        with self._lock:
            return self._active is not None and (owner is None or self._active.owner is owner)

    def submit(
        self,
        owner: object,
        label: str,
        work: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[BaseException], None],
    ) -> bool:
        operation = self.begin(owner, label)
        if operation is None:
            return False

        def run() -> None:
            try:
                self._completions.put((operation, work(), None, on_success, on_error))
            except BaseException as error:
                self._completions.put((operation, None, error, on_success, on_error))

        try:
            Thread(target=run, daemon=True).start()
        except BaseException:
            self.finish(operation.id)
            raise
        return True

    def drain(self, widget_exists=lambda owner: True) -> None:
        while not self._completions.empty():
            operation, result, error, on_success, on_error = self._completions.get()
            try:
                if widget_exists(operation.owner):
                    (on_error if error else on_success)(error if error else result)
            finally:
                self.finish(operation.id)


operations = OperationCoordinator()
