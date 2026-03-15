"""
Frame del módulo Comprimir.
"""

import threading
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from modules.compress import (
    comprimir_imagen, estimar_tamano, formatear_bytes, FORMATOS_SALIDA
)
from ui import colors, fonts


class CompressFrame(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._imagenes: list[str] = []
        self._formato: ctk.StringVar = ctk.StringVar(value='WEBP')
        self._calidad: ctk.IntVar = ctk.IntVar(value=85)
        self._quitar_exif: ctk.BooleanVar = ctk.BooleanVar(value=True)
        self._preview_img: ctk.CTkImage | None = None
        self._build()

    # ─── BUILD ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(
            self,
            text='Comprimir',
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, padx=28, pady=(26, 16), sticky='w')

        # Drop zone
        self._drop_zone = ctk.CTkFrame(
            self,
            height=120,
            corner_radius=12,
            border_width=1,
            border_color=colors.ACENTO_DIMMED,
            fg_color=colors.PANEL_BG,
            cursor='hand2'
        )
        self._drop_zone.grid(row=1, column=0, padx=28, sticky='ew')
        self._drop_zone.grid_propagate(False)
        self._drop_zone.grid_columnconfigure(0, weight=1)
        self._drop_zone.grid_rowconfigure(0, weight=1)

        # Estado vacío
        self._frame_vacio = ctk.CTkFrame(self._drop_zone, fg_color='transparent')
        self._frame_vacio.grid(row=0, column=0)
        ctk.CTkLabel(
            self._frame_vacio,
            text='+',
            font=ctk.CTkFont(size=28, weight='bold'),
            text_color=colors.ACENTO_DIMMED,
            fg_color='transparent'
        ).pack()
        ctk.CTkLabel(
            self._frame_vacio,
            text='Arrastrá imágenes acá  ·  o hacé clic para explorar',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            fg_color='transparent'
        ).pack(pady=(4, 0))

        # Estado con imagen cargada
        self._frame_preview = ctk.CTkFrame(self._drop_zone, fg_color='transparent')
        self._frame_preview.grid_columnconfigure(1, weight=1)

        self._canvas_preview = ctk.CTkLabel(
            self._frame_preview, text='',
            width=80, height=80,
            fg_color='transparent'
        )
        self._canvas_preview.grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=10)

        ctk.CTkLabel(
            self._frame_preview,
            text='Imagen cargada',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            fg_color='transparent', anchor='w'
        ).grid(row=0, column=1, sticky='w', pady=(14, 0))

        self._lbl_preview_nombre = ctk.CTkLabel(
            self._frame_preview, text='',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color='transparent', anchor='w'
        )
        self._lbl_preview_nombre.grid(row=1, column=1, sticky='w')

        self._lbl_preview_tam = ctk.CTkLabel(
            self._frame_preview, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.ACENTO,
            fg_color='transparent', anchor='w'
        )
        self._lbl_preview_tam.grid(row=2, column=1, sticky='w', pady=(0, 14))

        for w in (self._drop_zone, self._frame_vacio, self._frame_preview,
                  self._canvas_preview, self._lbl_preview_nombre, self._lbl_preview_tam):
            w.bind('<Button-1>', lambda _: self._explorar())

        self._mostrar_vacio()

        # Lista de archivos
        self._lista_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.ACENTO_DIMMED,
            height=80
        )
        self._lista_frame.grid(row=2, column=0, padx=28, pady=(10, 0), sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = ctk.CTkLabel(
            self._lista_frame,
            text='Sin imágenes cargadas',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_lista_vacia.pack(pady=8)

        # Panel de opciones
        self._panel_opciones = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_opciones.grid(row=3, column=0, padx=28, pady=(10, 0), sticky='ew')
        self._panel_opciones.grid_columnconfigure(1, weight=1)
        self._construir_opciones()

        # Info estimado
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=4, column=0, pady=(10, 4))

        # Botón
        self._btn_comprimir = ctk.CTkButton(
            self,
            text='Comprimir',
            height=44,
            corner_radius=10,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._comprimir
        )
        self._btn_comprimir.grid(row=5, column=0, padx=28, pady=(0, 26), sticky='ew')

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
            variable=self._calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
        )
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text='85',
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

        ctk.CTkLabel(
            p, text='Formato',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')

        self._seg_formato = ctk.CTkSegmentedButton(
            p,
            values=FORMATOS_SALIDA,
            variable=self._formato,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            text_color_disabled=colors.TEXT_GRAY,
            command=lambda _: self._actualizar_estimado(),
        )
        self._seg_formato.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='w')

        ctk.CTkLabel(
            p, text='Quitar EXIF',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=2, column=0, padx=(16, 12), pady=(8, 16), sticky='w')

        ctk.CTkSwitch(
            p, text='',
            variable=self._quitar_exif,
            onvalue=True, offvalue=False,
            progress_color=colors.ACENTO,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            fg_color=colors.SIDEBAR_SEPARATOR,
        ).grid(row=2, column=1, padx=(0, 16), pady=(8, 16), sticky='w')

    # ─── HELPERS PREVIEW ──────────────────────────────────────────────────────

    def _mostrar_vacio(self):
        self._frame_preview.grid_remove()
        self._frame_vacio.grid(row=0, column=0)
        self._drop_zone.configure(border_color=colors.ACENTO_DIMMED)

    def _mostrar_preview(self, ruta: str):
        self._frame_vacio.grid_remove()
        self._frame_preview.grid(row=0, column=0, sticky='ew')
        self._drop_zone.configure(border_color=colors.ACENTO)

        img = Image.open(ruta)
        img.thumbnail((80, 80), Image.Resampling.LANCZOS)
        self._preview_img = ctk.CTkImage(
            light_image=img, dark_image=img,
            size=(img.width, img.height)
        )
        self._canvas_preview.configure(image=self._preview_img)

        p = Path(ruta)
        nombre = p.name if len(p.name) <= 34 else p.name[:31] + '...'
        self._lbl_preview_nombre.configure(text=nombre)
        self._lbl_preview_tam.configure(text=formatear_bytes(p.stat().st_size))

    # ─── LÓGICA ───────────────────────────────────────────────────────────────

    def _explorar(self):
        archivos = filedialog.askopenfilenames(
            title='Seleccioná imágenes',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif')]
        )
        if archivos:
            self._cargar_imagenes(list(archivos))

    def _cargar_imagenes(self, rutas: list[str]):
        self._imagenes = rutas
        self._mostrar_preview(rutas[0])

        for w in self._lista_frame.winfo_children():
            w.destroy()

        for ruta in rutas:
            p = Path(ruta)
            fila = ctk.CTkFrame(
                self._lista_frame, fg_color=colors.SIDEBAR_BG, corner_radius=6
            )
            fila.pack(fill='x', pady=2, padx=4)
            fila.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                fila, text=p.name,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_COLOR, anchor='w'
            ).grid(row=0, column=0, padx=(10, 4), pady=6, sticky='w')
            ctk.CTkLabel(
                fila, text=formatear_bytes(p.stat().st_size),
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY, anchor='e'
            ).grid(row=0, column=1, padx=(4, 10), pady=6, sticky='e')

        self._actualizar_estimado()

    def _actualizar_calidad(self, val):
        self._lbl_calidad.configure(text=str(int(val)))
        self._actualizar_estimado()

    def _actualizar_estimado(self, *_):
        if not self._imagenes:
            self._lbl_info.configure(text='')
            return
        try:
            estimado = sum(
                estimar_tamano(r, self._calidad.get(), self._formato.get())
                for r in self._imagenes
            )
            n = len(self._imagenes)
            self._lbl_info.configure(
                text=f'{n} imagen{"es" if n > 1 else ""} · '
                     f'estimado {formatear_bytes(estimado)}'
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
            fmt = self._formato.get()
            ext = '.jpg' if fmt == 'JPEG' else f'.{fmt.lower()}'
            salida = str(Path(carpeta) / (p.stem + '_comprimido' + ext))
            res = comprimir_imagen(
                ruta, salida,
                calidad=self._calidad.get(),
                formato=fmt,
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