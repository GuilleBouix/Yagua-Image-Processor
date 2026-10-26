"""Small UI updates and a reusable pool of visible rows."""
from __future__ import annotations

import math
import tkinter as tk
from time import perf_counter
from typing import Any
import customtkinter as ctk

from app.ui.lifetime import UiLifetime


def configure_changed(widget, **values):
    changes = {key: value for key, value in values.items() if widget.cget(key) != value}
    if changes:
        widget.configure(**changes)


class StableRender:
    """One render after two equal, mapped viewport samples, 16 ms apart.

    Pixel updates never drive layout. Hidden widgets don't poll; Map or an
    explicit activation starts measuring again. All callbacks stay on Tk.
    """

    def __init__(self, owner, viewport, draw):
        self.owner, self.viewport, self.draw = owner, viewport, draw
        self.enabled = True
        self.job = None
        self.sample = None
        self.closed = False
        viewport.bind('<Configure>', self.request, add='+')
        viewport.bind('<Map>', self.request, add='+')
        viewport.bind('<Unmap>', self.cancel, add='+')
        viewport.bind('<Destroy>', self._destroyed, add='+')

    def set_visible(self, visible):
        self.enabled = visible
        if visible:
            self.request()
        else:
            self.cancel()

    def cancel(self, _event=None):
        if self.job is not None:
            self.owner.after_cancel(self.job)
            self.job = None
        self.sample = None

    def request(self, _event=None):
        if self.closed or not self.enabled or not self.viewport.winfo_ismapped():
            return
        size = (self.viewport.winfo_width(), self.viewport.winfo_height(),
                self.viewport._get_widget_scaling())
        # Repeated Map/Configure or content requests at an unchanged size do
        # not invalidate the first stable sample. A real geometry/scale change
        # still restarts the two-sample check.
        if self.sample != size:
            self.sample = None
        if self.job is None:
            self.job = self.owner.after(16, self._at_idle)

    def _at_idle(self):
        # Configure/layout idle handlers must run before sampling. Under load,
        # a timer can fire twice while Tk still has geometry work queued.
        self.job = self.owner.after_idle(self._measure)

    def _measure(self):
        self.job = None
        if self.closed or not self.enabled or not self.viewport.winfo_ismapped():
            self.sample = None
            return
        width, height = self.viewport.winfo_width(), self.viewport.winfo_height()
        if width <= 1 or height <= 1:
            self.sample = None
            # A mapped frame can briefly retain a 1px allocation while its
            # parent finishes the tab/layout update, with no later Configure.
            self.job = self.owner.after(32, self._at_idle)
            return
        size = (width, height, self.viewport._get_widget_scaling())
        if self.sample == size:
            self.sample = None
            self.draw(size)
        else:
            self.sample = size
            self.job = self.owner.after(16, self._at_idle)

    def _destroyed(self, _event):
        # CTkFrame forwards bindings to its internal canvas.
        self.cancel()
        self.closed = True


def activate_tab(frames, selected):
    """Switch existing panels without hiding and remapping the active one."""
    for name, frame in frames.items():
        if name != selected and frame.winfo_manager():
            frame.grid_remove()
    current = frames[selected]
    if not current.winfo_manager():
        current.grid()
    current.tkraise()


class PooledRow(ctk.CTkFrame):
    """Typed row slots used by the different list presentations."""
    key: Any = None
    thumb: ctk.CTkLabel
    name_label: ctk.CTkLabel
    info_label: ctk.CTkLabel
    status_label: ctk.CTkLabel
    original_label: ctk.CTkLabel
    new_label: ctk.CTkLabel
    variable: ctk.BooleanVar
    photo: ctk.CTkImage | None = None
    request_key: Any = None
    _placement: tuple | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)

    def release(self):
        if hasattr(self, 'thumb'):
            self.thumb.configure(image=None)
            self.thumb._label.configure(image='')
        self.photo = None


class VirtualRows(UiLifetime, tk.Frame):
    """Keep scroll extent for all items, widgets only for viewport + overscan.

    The factory returns a CTkFrame; render(row, key) binds its current model.
    The pool is bounded by viewport size, and keys survive sorting/appends.
    """
    def __init__(self, parent, factory, render, *, row_height=72, overscan=2):
        # A CTkFrame allocates a full-height drawing canvas. That exceeds X11's
        # pixmap limit for long lists; this plain frame only holds the extent.
        super().__init__(parent, bg=tk.Frame.cget(parent, 'background'), height=1, bd=0, highlightthickness=0)
        self._scroll_parent = parent
        self._extent = None
        self.pack(fill='x', expand=False)
        self.pack_propagate(False)
        self.factory, self.render_row = factory, render
        self.row_height, self.overscan = row_height, overscan
        self.keys: tuple = ()
        self.rows: dict = {}
        self.pool = []
        self.job = None
        self.on_destroy = lambda: None
        self.canvas = parent._parent_canvas
        self._previous_scroll = self.canvas.cget('yscrollcommand')
        self.canvas.configure(yscrollcommand=self._scroll_changed)
        self.canvas.bind('<Configure>', self.schedule, add='+')
        self.bind('<Map>', self.schedule, add='+')
        self.bind('<Configure>', self.schedule, add='+')

    def _get_widget_scaling(self):
        return self._scroll_parent._get_widget_scaling()

    def _apply_extent(self):
        extent = (len(self.keys), self._get_widget_scaling())
        if self._extent != extent:
            self._extent = extent
            self.configure(height=max(1, round(extent[0] * self.row_height * extent[1])))

    def _scroll_changed(self, first, last):
        if self._previous_scroll:
            self.tk.call(*self.tk.splitlist(self._previous_scroll), first, last)
        self.schedule()

    def sync(self, keys):
        keys = tuple(keys)
        if self.keys != keys:
            self.keys = keys
            self._apply_extent()
            for old in list(self.rows):
                if old not in keys:
                    row = self.rows.pop(old)
                    row.place_forget()
                    row.key = None
                    row.release()
                    self.pool.append(row)
        self.schedule()

    def schedule(self, _event=None):
        if self.job is None and self.winfo_exists():
            self.job = self.after_idle(self.refresh)

    def refresh(self, key=None):
        deadline = perf_counter() + .008
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        if not self.winfo_ismapped():
            return
        self._apply_extent()
        if key is not None:
            if key in self.rows:
                self.render_row(self.rows[key], key)
            return
        scale = self._get_widget_scaling()
        offset = max(0, self.canvas.canvasy(0) / scale)
        first = max(0, int(offset // self.row_height) - self.overscan)
        count = math.ceil(max(1, self.canvas.winfo_height()) / scale / self.row_height) + self.overscan * 2
        first = min(first, max(0, len(self.keys) - 1))
        visible = self.keys[first:first + count]
        for old in list(self.rows):
            if old not in visible:
                row = self.rows.pop(old)
                row.place_forget()
                row.key = None
                if hasattr(row, 'release'):
                    row.release()
                self.pool.append(row)
        for index, item in enumerate(visible, first):
            if perf_counter() >= deadline:
                self.job = self.after(1, self.refresh)
                break
            if item not in self.rows:
                row = self.pool.pop() if self.pool else self.factory(self)
                row.key = item
                self.rows[item] = row
            row = self.rows[item]
            placement = (index * self.row_height, self.row_height - 6)
            if getattr(row, '_placement', None) != placement or not row.winfo_ismapped():
                configure_changed(row, height=placement[1])
                row.place(x=0, y=placement[0], relwidth=1)
                row._placement = placement
            self.render_row(row, item)

    def destroy(self):
        self.on_destroy()
        self.canvas.configure(yscrollcommand=self._previous_scroll)
        super().destroy()
