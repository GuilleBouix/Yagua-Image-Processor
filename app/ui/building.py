"""Cooperative widget construction. Tk work always stays on the UI thread."""
from __future__ import annotations

from collections.abc import Callable, Generator
from functools import wraps
from time import perf_counter
from tkinter import TclError
from typing import Any


def finish(iterator):
    """Keep ordinary constructors synchronous, including their return values."""
    while True:
        try:
            next(iterator)
        except StopIteration as result:
            return result.value


def stepwise(function: Callable[..., Generator[Any, Any, Any]]) -> Any:
    @wraps(function)
    def synchronous(*args, **kwargs):
        return finish(function(*args, **kwargs))
    return synchronous


def steps_for(method, *args, **kwargs):
    function = getattr(method, '__wrapped__', None)
    if function is not None:
        return (yield from function(method.__self__, *args, **kwargs))
    result = method(*args, **kwargs)
    yield
    return result


class BuildTask:
    """One resumable construction, with one owned timer and an 8 ms budget."""
    def __init__(self, owner, iterator, on_done, on_error):
        self.owner, self.iterator = owner, iterator
        self.on_done, self.on_error = on_done, on_error
        self.job = None
        self.paused = True
        self.finished = False
        self.max_step_ms = 0.0
        self.max_batch_ms = 0.0
        self.slow_steps = []

    def resume(self):
        if self.finished:
            return
        self.paused = False
        if self.job is None:
            self.job = self.owner.after_idle(self._schedule_batch)

    def _schedule_batch(self):
        # Let Tk settle the previous batch before constructing more controls.
        # CTk scrollbars flush idle geometry internally; otherwise that work
        # accumulates and one innocent widget can block for hundreds of ms.
        self.job = None
        if not self.finished and not self.paused:
            self.job = self.owner.after(1, self._advance)

    def pause(self):
        self.paused = True
        if self.job is not None:
            try:
                self.owner.after_cancel(self.job)
            except TclError:
                pass
            self.job = None

    def cancel(self):
        self.pause()
        self.finished = True
        self.iterator.close()

    def _advance(self):
        self.job = None
        if self.paused or self.finished:
            return
        start = perf_counter()
        try:
            while not self.paused and perf_counter() - start < .008:
                before = perf_counter()
                next(self.iterator)
                elapsed = (perf_counter() - before) * 1000
                self.max_step_ms = max(self.max_step_ms, elapsed)
                if elapsed > 30 and len(self.slow_steps) < 12:
                    iterator = self.iterator
                    while getattr(iterator, 'gi_yieldfrom', None) is not None:
                        iterator = iterator.gi_yieldfrom
                    frame = getattr(iterator, 'gi_frame', None)
                    if frame is not None:
                        self.slow_steps.append((frame.f_code.co_filename, frame.f_lineno, round(elapsed, 2)))
        except StopIteration:
            self.finished = True
            try:
                self.on_done()
            except Exception as error:
                self.on_error(error)
        except Exception as error:
            self.finished = True
            self.on_error(error)
        finally:
            self.max_batch_ms = max(self.max_batch_ms, (perf_counter() - start) * 1000)
        if not self.finished and not self.paused:
            self.job = self.owner.after_idle(self._schedule_batch)
