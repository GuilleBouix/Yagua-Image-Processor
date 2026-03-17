"""
Helpers para listas de archivos con thumbnails.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.modules.compress import formatear_bytes


def clear_file_list(container: ctk.CTkScrollableFrame, filas: list[ctk.CTkLabel], thumbs: list[ctk.CTkImage]) -> None:
    for w in container.winfo_children():
        w.destroy()
    filas.clear()
    thumbs.clear()


def add_file_row(
    container: ctk.CTkScrollableFrame,
    ruta: str,
    filas: list[ctk.CTkLabel],
    *,
    name_max: int = 32,
    thumb_size: int = 44,
    show_ext: bool = True,
) -> None:
    p = Path(ruta)
    fila = ctk.CTkFrame(container, fg_color=colors.SIDEBAR_BG, corner_radius=8)
    fila.pack(fill='x', pady=3, padx=2)
    fila.grid_columnconfigure(1, weight=1)

    lbl_thumb = ctk.CTkLabel(fila, text='', width=thumb_size, height=thumb_size, fg_color='transparent')
    lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

    info = ctk.CTkFrame(fila, fg_color='transparent')
    info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

    nombre = p.name if len(p.name) <= name_max else p.name[: name_max - 3] + '...'
    ctk.CTkLabel(
        info, text=nombre,
        font=fonts.FUENTE_BASE,
        text_color=colors.TEXT_COLOR, anchor='w'
    ).pack(anchor='w')

    size_txt = formatear_bytes(p.stat().st_size)
    if show_ext:
        ext = p.suffix.upper().lstrip(".")
        meta_txt = f'{size_txt}  Â·  {ext}'
    else:
        meta_txt = size_txt
    ctk.CTkLabel(
        info,
        text=meta_txt,
        font=fonts.FUENTE_CHICA,
        text_color=colors.TEXT_GRAY, anchor='w'
    ).pack(anchor='w')

    filas.append(lbl_thumb)


def build_file_list(
    container: ctk.CTkScrollableFrame,
    rutas: list[str],
    filas: list[ctk.CTkLabel],
    thumbs: list[ctk.CTkImage],
    *,
    name_max: int = 32,
    thumb_size: int = 44,
    show_ext: bool = True,
) -> None:
    clear_file_list(container, filas, thumbs)
    for ruta in rutas:
        add_file_row(
            container, ruta, filas,
            name_max=name_max,
            thumb_size=thumb_size,
            show_ext=show_ext,
        )


def load_thumbs_async(
    rutas: list[str],
    filas: list[ctk.CTkLabel],
    thumbs: list[ctk.CTkImage],
    after_fn: Callable[[int, Callable[[], None]], None],
    *,
    thumb_size: int = 44,
) -> None:
    def _worker():
        local_thumbs: list[ctk.CTkImage | None] = []
        for ruta in rutas:
            try:
                with Image.open(ruta) as img:
                    img = img.copy()
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(thumb_size, thumb_size))
            except Exception:
                thumb = None
            local_thumbs.append(thumb)

        def _apply():
            thumbs[:] = [t for t in local_thumbs if t]
            for i, thumb in enumerate(local_thumbs):
                if thumb and i < len(filas):
                    filas[i].configure(image=thumb)

        after_fn(0, _apply)

    threading.Thread(target=_worker, daemon=True).start()
