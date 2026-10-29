"""Actualizaciones visuales pequeñas y reciclaje de filas visibles de listas."""
from __future__ import annotations

import math
import tkinter as tk
from time import perf_counter
from typing import Any
import customtkinter as ctk

from app.ui.lifetime import UiLifetime


def configure_changed(widget, **values):
    """Evita redibujos de widgets cuando los valores pedidos ya son iguales."""
    changes = {key: value for key, value in values.items() if widget.cget(key) != value}
    if changes:
        widget.configure(**changes)


class StableRender:
    """Dibuja una vez cuando dos mediciones del viewport coinciden con 16 ms de diferencia."""

    def __init__(self, owner, viewport, draw):
        """Conecta eventos de tamaño y guarda la función de dibujo pendiente."""
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
        """Pausa el render cuando el módulo está oculto."""
        self.enabled = visible
        if visible:
            self.request()
        else:
            self.cancel()

    def cancel(self, _event=None):
        """Cancela una solicitud de render pendiente."""
        if self.job is not None:
            self.owner.after_cancel(self.job)
            self.job = None
        self.sample = None

    def request(self, _event=None):
        """Agrupa eventos próximos antes de medir y volver a dibujar."""
        if self.closed or not self.enabled or not self.viewport.winfo_ismapped():
            return
        size = (self.viewport.winfo_width(), self.viewport.winfo_height(),
                self.viewport._get_widget_scaling())
        # Repeated Map/Configure or content requests at an unchanged size do
        # no invalide la primera muestra estable. Un cambio real de geometría o escala
        # reinicia la comprobación de dos muestras.
        if self.sample != size:
            self.sample = None
        if self.job is None:
            self.job = self.owner.after(16, self._at_idle)

    def _at_idle(self):
        # Los callbacks idle de geometría deben ejecutarse antes de medir. Con carga,
        # un timer puede dispararse dos veces mientras Tk aún tiene geometría pendiente.
        """Programa el render cuando Tk termina tareas prioritarias."""
        self.job = self.owner.after_idle(self._measure)

    def _measure(self):
        """Dibuja usando las dimensiones actuales del viewport."""
        self.job = None
        if self.closed or not self.enabled or not self.viewport.winfo_ismapped():
            self.sample = None
            return
        width, height = self.viewport.winfo_width(), self.viewport.winfo_height()
        if width <= 1 or height <= 1:
            self.sample = None
            # Un frame visible puede conservar por un momento un ancho de 1 px mientras
            # su contenedor termina el cambio de pestaña sin emitir otro Configure.
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
        # CTkFrame reenvía los eventos al canvas interno.
        """Cancela trabajo diferido cuando se destruye el viewport."""
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
        """Inicializa la fila que puede soltarse y volver a usarse."""
        super().__init__(*args, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)

    def release(self):
        """Desvincula datos y oculta la fila para reciclarla."""
        if hasattr(self, 'thumb'):
            self.thumb.configure(image=None)
            self.thumb._label.configure(image='')
        self.photo = None


class VirtualRows(UiLifetime, tk.Frame):
    """Conserva el scroll de toda la lista y crea widgets solo para filas visibles y su margen."""
    def __init__(self, parent, factory, render, *, row_height=72, overscan=2):
        """Inicializa el viewport virtual y sus callbacks de desplazamiento."""
        super().__init__(parent, bg=tk.Frame.cget(parent, 'background'), height=1, bd=0, highlightthickness=0)
        self._scroll_parent = parent
        self._extent = None
        self._origin = 0
        self._closed = False
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
        self._canvas_configure = self.canvas.bind('<Configure>', self.schedule, add='+')
        self._canvas_map = self.canvas.bind('<Map>', self.schedule, add='+')
        # CTk normally derives the scrollregion from its physical child window.
        # Our logical range is independent of that bounded window's height.
        self._previous_parent_configure = parent.bind('<Configure>')
        self._parent_configure = parent.bind('<Configure>', self._apply_extent)
        self.bind('<Map>', self.schedule, add='+')
        self.bind('<Configure>', self.schedule, add='+')

    def _get_widget_scaling(self):
        """Obtiene la escala actual de Tk para calcular alturas físicas."""
        return self._scroll_parent._get_widget_scaling()

    def _apply_extent(self, _event=None):
        """Keep a logical scrollbar range without allocating a giant X11 surface."""
        if self._closed:
            return
        scale = self._get_widget_scaling()
        height = max(1, self.canvas.winfo_height())
        physical = max(1, height + math.ceil((self.overscan * 2 + 2) * self.row_height * scale))
        extent = (len(self.keys), scale, height, self.canvas.winfo_width())
        if self._extent != extent:
            self._extent = extent
            self.configure(height=min(physical, max(1, round(len(self.keys) * self.row_height * scale))))
        region = (0, 0, max(1, self.canvas.winfo_width()),
                  max(height, round(len(self.keys) * self.row_height * scale)))
        if tuple(map(float, self.canvas.cget('scrollregion').split())) != region:
            self.canvas.configure(scrollregion=region)

    def _scroll_changed(self, first, last):
        """Refresca las filas visibles cuando cambia el scroll."""
        if self._closed:
            return
        if self._previous_scroll:
            self.tk.call(*self.tk.splitlist(self._previous_scroll), first, last)
        self.schedule()

    def sync(self, keys):
        """Asocia claves de datos con el conjunto mínimo de widgets reutilizables."""
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
        """Agrupa cambios de tamaño antes de recalcular filas visibles."""
        if not self._closed and self.job is None and self.winfo_exists():
            self.job = self.after_idle(self.refresh)

    def refresh(self, key=None):
        """Vuelve a dibujar una fila concreta o todas las visibles."""
        deadline = perf_counter() + .008
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        if self._closed or not self.canvas.winfo_ismapped():
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
        # Move the small child window along the logical list. Row coordinates
        # stay local, below X11 drawable limits even at the end of a large batch.
        self._origin = first * self.row_height
        window = self._scroll_parent._create_window_id
        position = (0, round(self._origin * scale))
        if tuple(self.canvas.coords(window)) != position:
            self.canvas.coords(window, *position)
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
            placement = (index * self.row_height - self._origin, self.row_height - 6)
            if getattr(row, '_placement', None) != placement or not row.winfo_ismapped():
                configure_changed(row, height=placement[1])
                row.place(x=0, y=placement[0], relwidth=1)
                row._placement = placement
            self.render_row(row, item)

    def destroy(self):
        """Cancela callbacks y destruye las filas recicladas."""
        self._closed = True
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        self.canvas.unbind('<Configure>', self._canvas_configure)
        self.canvas.unbind('<Map>', self._canvas_map)
        self.on_destroy()
        self._scroll_parent.unbind('<Configure>', self._parent_configure)
        self._scroll_parent.tk.call('bind', self._scroll_parent._w, '<Configure>', self._previous_parent_configure)
        self.canvas.configure(yscrollcommand=self._previous_scroll)
        super().destroy()
