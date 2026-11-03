"""Placement shared by Yagua's own auxiliary windows."""
from __future__ import annotations

import re
import tkinter as tk


def center_on_parent(window, parent, *, modal=False):
    """Place the finished window over its owner using physical screen coordinates.

    Defer until content and minimum sizes have settled. Read raw Tk geometry:
    CTk's public geometry reverses DPI scaling for sizes, but coordinates remain
    physical pixels. Do not clamp to the primary screen, which would move dialogs
    away from owners on another monitor.
    """
    owner = parent.winfo_toplevel()
    if not window.winfo_ismapped():
        window.withdraw()
    job = None

    def size(widget):
        """Lee el tamaño físico y aplica la escala de respaldo de CustomTkinter."""
        geometry = str(widget.tk.call('wm', 'geometry', widget._w))
        match = re.match(r'(\d+)x(\d+)', geometry)
        width, height = (int(match[1]), int(match[2])) if match else (1, 1)
        # X11 reports 1x1 while withdrawn, even after geometry was configured.
        # CTk keeps the requested logical size; convert that fallback to pixels.
        apply_scale = getattr(widget, '_apply_window_scaling', lambda value: value)
        return (width if width > 1 else int(apply_scale(getattr(widget, '_current_width', widget.winfo_reqwidth()))),
                height if height > 1 else int(apply_scale(getattr(widget, '_current_height', widget.winfo_reqheight()))))

    def place():
        """Centra y muestra la ventana cuando su geometría ya está estable."""
        nonlocal job
        job = None
        try:
            if not window.winfo_exists() or not owner.winfo_exists():
                return
            window.update_idletasks()
            if not window.winfo_exists() or not owner.winfo_exists():
                return
            width, height = size(window)
            owner_width, owner_height = size(owner)
            x = owner.winfo_rootx() + (owner_width - width) // 2
            y = owner.winfo_rooty() + (owner_height - height) // 2
            window.geometry(f'+{x}+{y}')
            window.deiconify()
            window.lift()
            if modal:
                window.grab_set()
        except tk.TclError:
            # Closing the owner while layout settles must not leave a callback error.
            return

    def cancel(event):
        """Cancela la colocación diferida cuando se destruye la ventana."""
        nonlocal job
        if event.widget is window and job is not None:
            try:
                window.after_cancel(job)
            except tk.TclError:
                pass
            job = None

    window.bind('<Destroy>', cancel, add=True)
    job = window.after_idle(place)
