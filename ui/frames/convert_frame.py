"""
Frame del módulo Convertir.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from modules.convert import convertir_imagen, FORMATOS_DESTINO
from modules.compress import formatear_bytes
from ui import colors, fonts
from utils import tintar_icono


class ConvertFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._imagenes: list[str] = []
        self._fmt_destino: ctk.StringVar = ctk.StringVar(value='WEBP')
        self._calidad: ctk.IntVar = ctk.IntVar(value=90)
        self._thumbs: list[ctk.CTkImage] = []
        self._filas_lista: list[ctk.CTkLabel] = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=28, pady=(26, 8), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila_titulo,
            text='Convertir',
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_limpiar = ctk.CTkButton(
            fila_titulo,
            text='Limpiar',
            width=80, height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color='#FFFFFF',
            text_color='#1A1A1A',
            hover_color='#EEEEEE',
            border_width=0,
            command=self._limpiar
        )
        self._btn_limpiar.grid(row=0, column=1, sticky='e')

        self._btn_seleccionar = ctk.CTkButton(
            self,
            text='Seleccionar imágenes',
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
            command=self._explorar
        )
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=8, sticky='ew')

        self._lista_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=0,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.ACENTO_DIMMED,
            height=200
        )
        self._lista_frame.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = ctk.CTkLabel(
            self._lista_frame,
            text='Sin imágenes cargadas',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_lista_vacia.pack(pady=12)

        self._panel_opciones = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_opciones.grid(row=3, column=0, padx=28, pady=8, sticky='ew')
        self._panel_opciones.grid_columnconfigure(1, weight=1)
        self._construir_opciones()

        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=4, column=0, pady=(0, 4))

    def _construir_opciones(self):
        p = self._panel_opciones

        ctk.CTkLabel(
            p, text='Convertir a',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        self._seg_formato = ctk.CTkSegmentedButton(
            p,
            values=FORMATOS_DESTINO,
            variable=self._fmt_destino,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            text_color_disabled=colors.TEXT_GRAY,
            command=self._actualizar_info,
        )
        self._seg_formato.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')

        self._lbl_calidad_label = ctk.CTkLabel(
            p, text='Calidad',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        self._lbl_calidad_label.grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')

        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        fila_cal.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        self._slider = ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            variable=self._calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
        )
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text='90',
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

        self._btn_convertir = ctk.CTkButton(
            p,
            text='Convertir',
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._convertir
        )
        self._btn_convertir.grid(
            row=2, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

        self._actualizar_info()

    def _explorar(self):
        archivos = filedialog.askopenfilenames(
            title='Seleccioná imágenes',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.avif *.ico *.gif')]
        )
        if archivos:
            self._cargar_imagenes(list(archivos))

    def _cargar_imagenes(self, rutas: list[str]):
        self._imagenes = rutas
        self._thumbs.clear()
        self._filas_lista.clear()

        for w in self._lista_frame.winfo_children():
            w.destroy()

        for ruta in rutas:
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
            self._filas_lista.append(lbl_thumb)

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
                text=f'{formatear_bytes(p.stat().st_size)}  ·  {p.suffix.upper().lstrip(".")}',
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY, anchor='w'
            ).pack(anchor='w')

        threading.Thread(
            target=self._cargar_thumbs, args=(rutas,), daemon=True
        ).start()
        self._actualizar_info()

    def _cargar_thumbs(self, rutas: list[str]):
        thumbs = []
        for ruta in rutas:
            try:
                img = Image.open(ruta)
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
        self._lbl_lista_vacia.pack(pady=12)
        self._lbl_info.configure(text='')

    def _actualizar_calidad(self, val):
        self._lbl_calidad.configure(text=str(int(val)))

    def _actualizar_info(self, *_):
        fmt = self._fmt_destino.get()
        sin_calidad = {'PNG', 'ICO', 'BMP', 'GIF'}
        tiene_calidad = fmt not in sin_calidad
        self._slider.configure(state='normal' if tiene_calidad else 'disabled')
        self._lbl_calidad_label.configure(
            text_color=colors.TEXT_GRAY if tiene_calidad else colors.ACENTO_DIMMED
        )
        self._lbl_calidad.configure(
            text_color=colors.ACENTO if tiene_calidad else colors.ACENTO_DIMMED
        )
        if self._imagenes:
            n = len(self._imagenes)
            self._lbl_info.configure(
                text=f'{n} imagen{"es" if n > 1 else ""} → {fmt}'
            )

    def _convertir(self):
        if not self._imagenes:
            self._lbl_info.configure(text='Primero cargá al menos una imagen.')
            return
        carpeta = filedialog.askdirectory(title='Elegí carpeta de salida')
        if not carpeta:
            return
        self._btn_convertir.configure(state='disabled', text='Convirtiendo...')
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta: str):
        errores = 0
        for ruta in self._imagenes:
            try:
                convertir_imagen(
                    ruta,
                    fmt_destino=self._fmt_destino.get(),
                    carpeta_salida=carpeta,
                    calidad=self._calidad.get()
                )
            except Exception:
                errores += 1

        n = len(self._imagenes)
        fmt = self._fmt_destino.get()
        ok = n - errores
        self.after(0, lambda: self._finalizar(ok, errores, fmt))

    def _finalizar(self, ok, errores, fmt):
        self._btn_convertir.configure(state='normal', text='Convertir')
        msg = f'{ok} imagen{"es" if ok != 1 else ""} convertida{"s" if ok != 1 else ""} a {fmt}'
        if errores:
            msg += f'  ·  {errores} con error'
        self._lbl_info.configure(text=msg)
