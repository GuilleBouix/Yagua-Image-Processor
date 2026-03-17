"""
Frame del módulo Extraer Paleta de Colores.
"""

import threading
from pathlib import Path
from tkinter import filedialog
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from modules.palette import extraer_paleta, exportar_paleta_imagen, formatos_color, es_color_claro, rgb_a_hex
from ui import colors, fonts
from utils import tintar_icono


class PaletteFrame(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._ruta: str | None = None
        self._preview_img: ctk.CTkImage | None = None
        self._paleta: list[tuple[int, int, int]] = []
        self._build()

    # ─── BUILD ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Título + limpiar
        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=28, pady=(26, 8), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila_titulo,
            text='Paleta de colores',
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

        # Zona de carga
        self._btn_seleccionar = ctk.CTkButton(
            self,
            text='Seleccionar imagen',
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

        # Preview de imagen cargada
        self._frame_preview = ctk.CTkFrame(
            self,
            height=110,
            corner_radius=12,
            border_width=1,
            border_color=colors.ACENTO_DIMMED,
            fg_color=colors.PANEL_BG,
        )
        self._frame_preview.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._frame_preview.grid_propagate(False)
        self._frame_preview.grid_columnconfigure(0, weight=1)
        self._frame_preview.grid_columnconfigure(1, weight=1)
        self._frame_preview.grid_rowconfigure(0, weight=1)

        self._lbl_preview = ctk.CTkLabel(
            self._frame_preview, text='',
            width=80, height=80, fg_color='transparent'
        )
        self._lbl_preview.grid(row=0, column=0, padx=(14, 12), pady=10, sticky='w')

        self._lbl_nombre = ctk.CTkLabel(
            self._frame_preview, text='',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color='transparent', anchor='w'
        )
        self._lbl_nombre.grid(row=0, column=1, sticky='w', pady=(16, 2))

        self._lbl_meta = ctk.CTkLabel(
            self._frame_preview, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            fg_color='transparent', anchor='w'
        )
        self._lbl_meta.grid(row=0, column=1, sticky='w', pady=(38, 0))

        self._mostrar_vacio()

        # Panel de paleta
        self._panel_paleta = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_paleta.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._panel_paleta.grid_columnconfigure(0, weight=1)
        self._construir_panel_paleta()

        # Info
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=3, column=0, pady=(0, 4))

    def _construir_panel_paleta(self):
        p = self._panel_paleta

        # Selector de cantidad de colores
        fila_top = ctk.CTkFrame(p, fg_color='transparent')
        fila_top.grid(row=0, column=0, padx=16, pady=(14, 8), sticky='ew')
        fila_top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila_top, text='Colores a extraer',
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._seg_n = ctk.CTkSegmentedButton(
            fila_top,
            values=['4', '6', '8', '10', '12'],
            font=fonts.FUENTE_CHICA,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._auto_extraer  # cambia N → re-extrae automáticamente
        )
        self._seg_n.set('6')
        self._seg_n.grid(row=0, column=1, sticky='e')

        # Contenedor de swatches
        self._swatches_frame = ctk.CTkFrame(p, fg_color='transparent')
        self._swatches_frame.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')

        ctk.CTkLabel(
            self._swatches_frame,
            text='Cargá una imagen para ver la paleta',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=20)

        # Botón — guarda la paleta como imagen PNG
        self._btn_guardar = ctk.CTkButton(
            p,
            text='Guardar paleta como imagen',
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._guardar_imagen
        )
        self._btn_guardar.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='ew')

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    def _mostrar_vacio(self):
        self._frame_preview.configure(border_color=colors.ACENTO_DIMMED)
        self._lbl_preview.configure(image='')
        self._lbl_nombre.configure(text='Sin imagen seleccionada')
        self._lbl_meta.configure(text='Seleccioná una imagen para ver la paleta')

    def _mostrar_cargado(self, ruta: str):
        self._frame_preview.configure(border_color=colors.ACENTO)

        img = Image.open(ruta)
        w, h = img.size
        img.thumbnail((80, 80), Image.Resampling.LANCZOS)
        self._preview_img = ctk.CTkImage(
            light_image=img, dark_image=img,
            size=(img.width, img.height)
        )
        self._lbl_preview.configure(image=self._preview_img)

        p = Path(ruta)
        nombre = p.name if len(p.name) <= 34 else p.name[:31] + '...'
        self._lbl_nombre.configure(text=nombre)
        self._lbl_meta.configure(text=f'{w} × {h} px  ·  {p.suffix.upper().lstrip(".")}')

    def _renderizar_paleta(self, paleta: list[tuple[int, int, int]]):
        for w in self._swatches_frame.winfo_children():
            w.destroy()

        n = len(paleta)
        self._swatches_frame.grid_columnconfigure(
            tuple(range(n)), weight=1
        )

        for i, rgb in enumerate(paleta):
            hex_color = rgb_a_hex(rgb)

            col = ctk.CTkFrame(
                self._swatches_frame, corner_radius=10, fg_color='transparent'
            )
            col.grid(row=0, column=i, padx=2, pady=(4, 8), sticky='nsew')
            col.grid_columnconfigure(0, weight=1)

            canvas = tk.Canvas(
                col, width=50, height=50,
                bg=hex_color, highlightthickness=0, bd=0, cursor='hand2'
            )
            canvas.grid(row=0, column=0, sticky='ew', ipady=6)
            canvas.create_rectangle(0, 0, 200, 200, fill=hex_color, outline='')

            ctk.CTkLabel(
                col, text=hex_color,
                font=ctk.CTkFont(size=9),
                text_color=colors.TEXT_GRAY,
                fg_color='transparent'
            ).grid(row=1, column=0, pady=(3, 2))

            for fmt, valor in formatos_color(rgb).items():
                ctk.CTkButton(
                    col,
                    text=fmt,
                    width=50, height=20,
                    corner_radius=6,
                    font=ctk.CTkFont(size=9),
                    fg_color=colors.SIDEBAR_BG,
                    hover_color=colors.SIDEBAR_HOVER,
                    text_color=colors.TEXT_GRAY,
                    command=lambda v=valor: self._copiar(v)
                ).grid(row=col.grid_size()[1], column=0, pady=1, sticky='ew')

    def _copiar(self, valor: str):
        self.clipboard_clear()
        self.clipboard_append(valor)
        self._lbl_info.configure(text=f'Copiado: {valor}')
        self.after(2000, lambda: self._lbl_info.configure(text=f'{len(self._paleta)} colores extraídos — hacé clic en un formato para copiar'))

    # ─── LÓGICA ───────────────────────────────────────────────────────────────

    def _explorar(self):
        archivo = filedialog.askopenfilename(
            title='Seleccioná una imagen',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif')]
        )
        if not archivo:
            return
        self._ruta = archivo
        self._paleta = []
        self._mostrar_cargado(archivo)
        # Extraer automáticamente al cargar
        n = int(self._seg_n.get())
        threading.Thread(target=self._proceso_extraccion, args=(n,), daemon=True).start()

    def _auto_extraer(self, *_):
        """Se llama al cambiar N — re-extrae si hay imagen cargada."""
        if not self._ruta:
            return
        n = int(self._seg_n.get())
        threading.Thread(target=self._proceso_extraccion, args=(n,), daemon=True).start()

    def _proceso_extraccion(self, n: int):
        try:
            paleta = extraer_paleta(self._ruta, n)  # type: ignore
            self.after(0, lambda: self._aplicar_paleta(paleta))
        except Exception as e:
            self.after(0, lambda: self._lbl_info.configure(text=f'Error: {e}'))

    def _aplicar_paleta(self, paleta: list[tuple[int, int, int]]):
        self._paleta = paleta
        self._renderizar_paleta(paleta)
        self._lbl_info.configure(
            text=f'{len(paleta)} colores extraídos — hacé clic en un formato para copiar'
        )

    def _guardar_imagen(self):
        if not self._paleta:
            self._lbl_info.configure(text='Primero cargá una imagen.')
            return
        ruta = filedialog.asksaveasfilename(
            title='Guardar paleta',
            defaultextension='.png',
            filetypes=[('PNG', '*.png')],
            initialfile='paleta.png'
        )
        if not ruta:
            return
        self._btn_guardar.configure(state='disabled', text='Guardando...')

        def _proceso():
            exportar_paleta_imagen(self._paleta, ruta)
            self.after(0, lambda: self._btn_guardar.configure(
                state='normal', text='Guardar Paleta de Colores'
            ))
            self.after(0, lambda: self._lbl_info.configure(
                text=f'Guardada como {Path(ruta).name}'
            ))

        threading.Thread(target=_proceso, daemon=True).start()

    def _limpiar(self):
        self._ruta = None
        self._paleta = []
        self._preview_img = None
        self._mostrar_vacio()
        for w in self._swatches_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._swatches_frame,
            text='Cargá una imagen para ver la paleta',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=20)
        self._lbl_info.configure(text='')