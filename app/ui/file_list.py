"""
Helpers para listas de archivos con thumbnails.
Contiene funciones para crear, poblar y limpiar listas de archivos.

Relacionado con:
    - app/ui/frames/base.py: Usa estas funciones para las listas de imagenes.
    - app/ui/frames/compress/frame.py: Lista de archivos a comprimir.
    - app/ui/frames/convert/frame.py: Lista de archivos a convertir.
    - app/ui/frames/resize/frame.py: Lista de archivos a redimensionar.
    - app/modules/compress.py: Usa formatear_bytes para mostrar tamanos.
"""

from __future__ import annotations

from pathlib import Path
import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.modules.compress import formatear_bytes
from app.ui.image_cache import ImageRequests
from app.ui.rendering import VirtualRows, PooledRow, configure_changed


class FileList:
    """File rows recycled as the viewport scrolls, with progressive thumbnails."""
    def __init__(self, container, filas, thumbs, *, corner_radius=8, design_system=False):
        self.filas, self.thumbs = filas, thumbs
        self.corner_radius = corner_radius
        self.design_system = design_system
        self.generation = 0
        self.statuses = {}
        for child in container.winfo_children():
            child.pack_forget()
            child.grid_forget()
        self.empty = ctk.CTkLabel(container, text=t('no_images'), font=fonts.FUENTE_CHICA,
                                   text_color=colors.TEXT_GRAY)
        self.virtual = VirtualRows(container, self._create, self._render, row_height=76)
        self.loader = ImageRequests(self.virtual)
        self.virtual.on_destroy = self.loader.cancel

    def _create(self, parent):
        from app.ui.styles import surface
        options = surface('row') if self.design_system else dict(
            fg_color=colors.SIDEBAR_BG, corner_radius=self.corner_radius)
        row = PooledRow(parent, **options)
        row.grid_columnconfigure(1, weight=1)
        row.thumb = ctk.CTkLabel(row, text='', width=44, height=44)
        row.thumb.grid(row=0, column=0, rowspan=2, padx=(8, 10), pady=6)
        row.name_label = ctk.CTkLabel(row, text='', width=1, anchor='w', font=fonts.FUENTE_BASE)
        row.name_label.grid(row=0, column=1, sticky='ew', padx=(0, 8), pady=(6, 0))
        row.info_label = ctk.CTkLabel(row, text='', width=1, anchor='w', font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY)
        row.info_label.grid(row=1, column=1, sticky='ew', padx=(0, 8), pady=(0, 6))
        row.photo = None
        row.request_key = None
        def release():
            row.thumb.configure(image=None)
            row.thumb._label.configure(image='')
            row.photo = None
            row.request_key = None
        row.release = release
        return row

    def _render(self, row, key):
        path, _occurrence = key
        request_key = (self.generation, key)
        if row.request_key == request_key:
            return
        if row.request_key is None or row.request_key[1] != key:
            row.release()
            configure_changed(row.info_label, text=Path(path).suffix.lstrip('.').upper())
        row.request_key = request_key
        name = Path(path).name
        configure_changed(row.name_label, text=name if len(name) <= 32 else name[:29] + '…')
        def loaded(result, error):
            if row.request_key != request_key or row.key != key:
                return
            if result is not None:
                if row.photo is None or row.photo.cget('light_image') is not result.image:
                    row.photo = ctk.CTkImage(light_image=result.image, dark_image=result.image, size=result.image.size)
                    row.thumb.configure(image=row.photo)
                status = self.statuses.get(path, '')
                configure_changed(row.info_label, text=f'{formatear_bytes(result.bytes)}  -  {result.format}' + (f' · {status}' if status else ''))
            else:
                configure_changed(row.info_label, text=self.statuses.get(path) or t('error_generic'))
            self.filas[:] = [item.thumb for item in self.virtual.rows.values()]
            self.thumbs[:] = [item.photo for item in self.virtual.rows.values() if item.photo is not None]
        self.loader.request(path, (44, 44), loaded)

    def sync(self, paths):
        self.generation += 1
        self.loader.cancel()
        seen, keys = {}, []
        for path in paths:
            path = str(path)
            occurrence = seen.get(path, 0)
            seen[path] = occurrence + 1
            keys.append((path, occurrence))
        self.virtual.sync(keys)
        if keys:
            self.empty.pack_forget()
        else:
            self.empty.pack(pady=12)
            self.filas.clear()
            self.thumbs.clear()


def clear_file_list(container, filas, thumbs):
    """
    Limpia una lista de archivos eliminando todos los widgets.
    
    Destruye todos los widgets hijos del contenedor y limpia
    las listas de referencias.
    
    Args:
        container: CTkScrollableFrame que contiene las filas.
        filas: Lista de labels de thumbnails a limpiar.
        thumbs: Lista de imagenes de thumbnails a limpiar.
    """
    # Destruir todos los widgets hijos
    for w in container.winfo_children():
        w.destroy()
    
    # Limpiar las listas de referencias
    filas.clear()
    thumbs.clear()


def add_file_row(container, ruta, filas, *, name_max=32, thumb_size=44, show_ext=True):
    """
    Agrega una fila de archivo a la lista.
    
    Crea una fila con thumbnail, nombre y tamano del archivo.
    
    Args:
        container: CTkScrollableFrame donde agregar la fila.
        ruta: Ruta del archivo a mostrar.
        filas: Lista donde guardar la referencia al label de thumbnail.
        name_max: Maximo caracteres del nombre de archivo.
        thumb_size: Tamano del thumbnail en pixeles.
        show_ext: Si es True, muestra la extension del archivo.
    """
    p = Path(ruta)
    
    # Crear frame para la fila
    fila = ctk.CTkFrame(container, fg_color=colors.SIDEBAR_BG, corner_radius=8)
    fila.pack(fill='x', pady=3, padx=2)
    fila.grid_columnconfigure(1, weight=1)

    # Label para el thumbnail
    lbl_thumb = ctk.CTkLabel(fila, text='', width=thumb_size, height=thumb_size, fg_color='transparent')
    lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

    # Frame para la informacion del archivo
    info = ctk.CTkFrame(fila, fg_color='transparent')
    info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

    # Truncar nombre si es muy largo
    nombre = p.name if len(p.name) <= name_max else p.name[: name_max - 3] + '...'
    
    # Label del nombre del archivo
    ctk.CTkLabel(
        info, text=nombre,
        font=fonts.FUENTE_BASE,
        text_color=colors.TEXT_COLOR, anchor='w'
    ).pack(anchor='w')

    # Obtener tamano formateado
    try:
        size_txt = formatear_bytes(p.stat().st_size)
    except OSError:
        size_txt = t('error_generic')
    
    # Construir texto de metadatos
    if show_ext:
        ext = p.suffix.upper().lstrip(".")
        meta_txt = f'{size_txt}  -  {ext}'
    else:
        meta_txt = size_txt
    
    # Label de metadatos (tamano y extension)
    ctk.CTkLabel(
        info,
        text=meta_txt,
        font=fonts.FUENTE_CHICA,
        text_color=colors.TEXT_GRAY, anchor='w'
    ).pack(anchor='w')

    # Guardar referencia al label de thumbnail
    filas.append(lbl_thumb)


def build_file_list(container, rutas, filas, thumbs, *, name_max=32, thumb_size=44, show_ext=True):
    """
    Construye una lista completa de archivos.
    
    Limpia la lista existente y agrega todas las filas nuevas.
    
    Args:
        container: CTkScrollableFrame donde construir la lista.
        rutas: Lista de rutas de archivos a mostrar.
        filas: Lista de labels de thumbnails.
        thumbs: Lista de imagenes de thumbnails.
        name_max: Maximo caracteres del nombre de archivo.
        thumb_size: Tamano del thumbnail en pixeles.
        show_ext: Si es True, muestra la extension del archivo.
    """
    # Limpiar lista existente
    clear_file_list(container, filas, thumbs)
    
    # Agregar fila para cada archivo
    for ruta in rutas:
        add_file_row(
            container, ruta, filas,
            name_max=name_max,
            thumb_size=thumb_size,
            show_ext=show_ext,
        )


def load_thumbs_async(rutas, filas, thumbs, after_fn, *, thumb_size=44):
    """
    Carga thumbnails en un hilo secundario para no bloquear la UI.
    
    Genera thumbnails de las imagenes en background y los aplica
    a los labels cuando estan listos.
    
    Args:
        rutas: Lista de rutas de archivos para generar thumbnails.
        filas: Lista de labels donde mostrar los thumbnails.
        thumbs: Lista donde guardar las imagenes de thumbnails.
        after_fn: Funcion para programar actualizaciones en el hilo principal.
        thumb_size: Tamano maximo del thumbnail en pixeles.
    """
    rows = tuple(filas)
    if not rows:
        return
    loader = ImageRequests(rows[0])
    for path, row in zip(tuple(rutas), rows):
        def loaded(result, error, row=row):
            if result is not None and tuple(filas) == rows and row.winfo_exists():
                photo = ctk.CTkImage(light_image=result.image, dark_image=result.image, size=result.image.size)
                thumbs.append(photo)
                row.configure(image=photo)
        loader.request(path, (thumb_size, thumb_size), loaded)
