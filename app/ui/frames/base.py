"""
Clase base para frames de la aplicaciÃ³n.
Contiene mÃ©todos y componentes comunes reutilizables.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.utils import tintar_icono
from app.modules.compress import formatear_bytes
from app.translations import t


class BaseFrame(ctk.CTkFrame):
    def __init__(self, parent, title: str):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._title = title
        self._imagenes: list[str] = []
        self._thumbs: list[ctk.CTkImage] = []
        self._filas_lista: list[ctk.CTkLabel] = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self):
        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=28, pady=(26, 8), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila_titulo,
            text=self._title,
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_limpiar = ctk.CTkButton(
            fila_titulo,
            text=t('clean'),
            width=80,
            height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=self._limpiar
        )
        self._btn_limpiar.grid(row=0, column=1, sticky='e')

    def _build_content(self):
        raise NotImplementedError("Subclasses must implement _build_content")

    def _build_footer(self):
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=100, column=0, pady=(0, 4))

    def _crear_boton_seleccionar(self, parent, texto: str | None = None, comando=None) -> ctk.CTkButton:
        if comando is None:
            comando = self._explorar
        if texto is None:
            texto = t('select_images')

        return ctk.CTkButton(
            parent,
            text=texto,
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            image=tintar_icono('assets/icons/upload.png', colors.ICON_COLOR),
            compound='left',
            command=comando
        )

    def _crear_lista_archivos(self, parent, height: int = 200) -> ctk.CTkScrollableFrame:
        lista = ctk.CTkScrollableFrame(
            parent,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            height=height
        )
        lista.grid_columnconfigure(0, weight=1)
        return lista

    def _crear_lista_vacia(self, parent) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )

    def _explorar(self, titulo: str | None = None, multi: bool = True):
        if titulo is None:
            titulo = t('select_images')
        if multi:
            archivos = filedialog.askopenfilenames(
                title=titulo,
                filetypes=[('ImÃ¡genes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif *.ico')]
            )
            if archivos:
                self._cargar_imagenes(list(archivos))
        else:
            archivo = filedialog.askopenfilename(
                title=titulo,
                filetypes=[('ImÃ¡genes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif')]
            )
            if archivo:
                self._cargar_imagenes([archivo])

    def _cargar_imagenes(self, rutas: list[str]):
        self._imagenes = rutas
        self._thumbs.clear()
        self._filas_lista.clear()

        for w in self._lista_frame.winfo_children():
            w.destroy()

        for ruta in rutas:
            self._agregar_fila_archivo(ruta)

        threading.Thread(
            target=self._cargar_thumbs_en_background,
            args=(rutas,),
            daemon=True
        ).start()

    def _agregar_fila_archivo(self, ruta: str):
        p = Path(ruta)
        fila = ctk.CTkFrame(
            self._lista_frame, fg_color=colors.SIDEBAR_BG, corner_radius=8
        )
        fila.pack(fill='x', pady=3, padx=2)
        fila.grid_columnconfigure(1, weight=1)

        lbl_thumb = ctk.CTkLabel(
            fila, text='', width=44, height=44, fg_color='transparent'
        )
        lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

        info = ctk.CTkFrame(fila, fg_color='transparent')
        info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

        nombre = p.name if len(p.name) <= 32 else p.name[:29] + '...'
        ctk.CTkLabel(
            info, text=nombre,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).pack(anchor='w')
        ctk.CTkLabel(
            info,
            text=f'{formatear_bytes(p.stat().st_size)}  Â·  {p.suffix.upper().lstrip(".")}',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).pack(anchor='w')

        self._filas_lista.append(lbl_thumb)

    def _cargar_thumbs_en_background(self, rutas: list[str]):
        thumbs = []
        for ruta in rutas:
            try:
                with Image.open(ruta) as img:
                    img = img.copy()
                img.thumbnail((44, 44), Image.Resampling.LANCZOS)
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(44, 44))
            except Exception:
                thumb = None
            thumbs.append(thumb)
        self.after(0, lambda: self._aplicar_thumbs(thumbs))

    def _aplicar_thumbs(self, thumbs):
        self._thumbs = [t for t in thumbs if t]
        for i, thumb in enumerate(thumbs):
            if thumb and i < len(self._filas_lista):
                self._filas_lista[i].configure(image=thumb)

    def _limpiar(self):
        self._imagenes = []
        self._thumbs.clear()
        self._filas_lista.clear()
        for w in self._lista_frame.winfo_children():
            w.destroy()
        if hasattr(self, '_lbl_lista_vacia'):
            self._lbl_lista_vacia.pack(pady=12)
        self._lbl_info.configure(text='')
