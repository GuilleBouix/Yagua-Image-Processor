"""Owned Tk timers are cancelled before a view is destroyed."""
import tkinter as tk
from typing import Any, Callable, Literal


class UiLifetime(tk.Misc):
    _owned_after: set[str]

    def after(self, ms: int | Literal["idle"], func: Callable[..., Any] | None = None, *args: Any) -> str:
        if func is None:
            return self.tk.call('after', ms)
        if not hasattr(self, '_owned_after'):
            self._owned_after = set()
        def deliver():
            self._owned_after.discard(job)
            if self.winfo_exists():
                func(*args)
        job = super().after(ms, deliver)
        self._owned_after.add(job)
        return job

    def after_cancel(self, job: str) -> None:
        if hasattr(self, '_owned_after'):
            self._owned_after.discard(job)
        return super().after_cancel(job)

    def destroy(self) -> None:
        for job in tuple(getattr(self, '_owned_after', ())):
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
        super().destroy()
