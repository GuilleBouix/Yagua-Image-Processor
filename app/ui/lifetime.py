"""Owned Tk timers are cancelled before a view is destroyed."""
import tkinter as tk
from typing import Any, Callable, Literal


class UiLifetime(tk.Misc):
    """Cancela los callbacks temporizados al destruir una vista."""
    _owned_after: set[str]

    def after(self, ms: int | Literal["idle"], func: Callable[..., Any] | None = None, *args: Any) -> str:
        """Registra callbacks y limpia su identificador al terminar."""
        if func is None:
            return self.tk.call('after', ms)
        if not hasattr(self, '_owned_after'):
            self._owned_after = set()
        def deliver():
            """Ejecuta el callback y retira su temporizador del registro local."""
            self._owned_after.discard(job)
            if self.winfo_exists():
                func(*args)
        job = super().after(ms, deliver)
        self._owned_after.add(job)
        return job

    def after_cancel(self, job: str) -> None:
        """Cancela el temporizador y elimina su referencia local."""
        if hasattr(self, '_owned_after'):
            self._owned_after.discard(job)
        return super().after_cancel(job)

    def destroy(self) -> None:
        """Cancela todos los temporizadores antes de destruir el widget."""
        for job in tuple(getattr(self, '_owned_after', ())):
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
        super().destroy()
