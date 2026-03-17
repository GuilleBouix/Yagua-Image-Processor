"""
Frame del módulo Comprimir.
"""

import threading
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from modules.compress import comprimir_imagen, estimar_tamano, formatear_bytes
from ui import colors, fonts
from utils import tintar_icono


class CompressFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._imagenes: list[str] = []
        self._calidad: ctk.IntVar = ctk.IntVar(value=60)
        self._quitar_exif: ctk.BooleanVar = ctk.BooleanVar(value=True)
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
            text='Comprimir',
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_limpiar = ctk.CTkButton(
            fila_titulo,
            text='Limpiar',
            width=80,
            height=30,
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
            p, text='Calidad',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        fila_cal.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        self._slider = ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            number_of_steps=9,
            variable=self._calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
        )
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text='60',
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

        ctk.CTkLabel(
            p, text='Quitar EXIF',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=(8, 16), sticky='w')

        ctk.CTkSwitch(
            p, text='',
            variable=self._quitar_exif,
            onvalue=True, offvalue=False,
            progress_color=colors.ACENTO,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            fg_color=colors.SIDEBAR_SEPARATOR,
        ).grid(row=1, column=1, padx=(0, 16), pady=(8, 16), sticky='w')

        self._btn_comprimir = ctk.CTkButton(
            p,
            text='Comprimir',
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._comprimir
        )
        self._btn_comprimir.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew')

    def _explorar(self):
        archivos = filedialog.askopenfilenames(
            title='Selecciona tus imágenes',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif *.ico')]
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

            self._filas_lista.append(lbl_thumb)

        threading.Thread(
            target=self._procesar_carga,
            args=(rutas,),
            daemon=True
        ).start()

    def _procesar_carga(self, rutas: list[str]):
        thumbs = []
        for ruta in rutas:
            try:
                img = Image.open(ruta)
                img.thumbnail((44, 44), Image.Resampling.LANCZOS)
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(44, 44))
            except Exception:
                thumb = None
            thumbs.append(thumb)

        estimado = 0
        for ruta in rutas:
            try:
                estimado += estimar_tamano(ruta, self._calidad.get())
            except Exception:
                pass

        self.after(0, lambda: self._aplicar_carga(thumbs, estimado, len(rutas)))

    def _aplicar_carga(self, thumbs, estimado, n):
        self._thumbs = [t for t in thumbs if t]

        for i, thumb in enumerate(thumbs):
            if thumb and i < len(self._filas_lista):
                self._filas_lista[i].configure(image=thumb)

        if estimado > 0:
            self._lbl_info.configure(
                text=f'{n} imagen{"es" if n > 1 else ""} · '
                    f'estimado {formatear_bytes(estimado)}'
            )

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
        self._actualizar_estimado()

    def _actualizar_estimado(self, *_):
        if not self._imagenes:
            self._lbl_info.configure(text='')
            return
        try:
            estimado = sum(estimar_tamano(r, self._calidad.get()) for r in self._imagenes)
            n = len(self._imagenes)
            self._lbl_info.configure(
                text=f'{n} imagen{"es" if n > 1 else ""} · estimado {formatear_bytes(estimado)}'
            )
        except Exception:
            pass

    def _comprimir(self):
        if not self._imagenes:
            self._lbl_info.configure(text='Primero cargá al menos una imagen.')
            return
        carpeta = filedialog.askdirectory(title='Elegí carpeta de salida')
        if not carpeta:
            return
        self._btn_comprimir.configure(state='disabled', text='Comprimiendo...')
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta: str):
        resultados = []
        for ruta in self._imagenes:
            p = Path(ruta)
            salida = str(Path(carpeta) / (p.stem + '_comprimido' + p.suffix))
            res = comprimir_imagen(
                ruta, salida,
                calidad=self._calidad.get(),
                quitar_exif=self._quitar_exif.get()
            )
            resultados.append(res)

        total_orig = sum(r['tam_original'] for r in resultados)
        total_comp = sum(r['tam_comprimido'] for r in resultados)
        reduccion = round((1 - total_comp / total_orig) * 100, 1)
        n = len(resultados)
        self.after(0, lambda: self._finalizar(n, total_orig, total_comp, reduccion))

    def _finalizar(self, n, orig, comp, reduccion):
        self._btn_comprimir.configure(state='normal', text='Comprimir')
        self._lbl_info.configure(
            text=f'{n} imagen{"es" if n > 1 else ""} · '
                 f'{formatear_bytes(orig)} → {formatear_bytes(comp)} · '
                 f'{reduccion}% más chico'
        )
