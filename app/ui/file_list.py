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

import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.modules.compress import formatear_bytes


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
    size_txt = formatear_bytes(p.stat().st_size)
    
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
    def _worker():
        """
        Worker que genera thumbnails en segundo plano.
        """
        local_thumbs = []
        
        # Generar thumbnail para cada archivo
        for ruta in rutas:
            try:
                # Abrir y copiar imagen
                with Image.open(ruta) as img:
                    img = img.copy()
                
                # Redimensionar manteniendo aspecto
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                
                # Crear CTkImage
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(thumb_size, thumb_size))
            except Exception:
                # Usar None si falla
                thumb = None
            
            local_thumbs.append(thumb)

        # Funcion para aplicar thumbnails en el hilo principal
        def _apply():
            # Actualizar lista de thumbnails
            thumbs[:] = [t for t in local_thumbs if t]
            
            # Aplicar thumbnail a cada label
            for indice, thumb in enumerate(local_thumbs):
                if thumb and indice < len(filas):
                    filas[indice].configure(image=thumb)

        # Programar aplicacion en hilo principal
        after_fn(0, _apply)

    # Iniciar worker en hilo daemon
    threading.Thread(target=_worker, daemon=True).start()
