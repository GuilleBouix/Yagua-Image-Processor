"""
Frame del módulo Metadatos EXIF.
Tabs: Ver · Editar · Limpiar
"""

import threading
from pathlib import Path
from tkinter import filedialog
import webbrowser

import customtkinter as ctk
from PIL import Image

from modules.metadata import (
    leer_metadatos, limpiar_exif, editar_exif,
    exportar_txt, exportar_json, CAMPOS_EDITABLES
)
from modules.compress import formatear_bytes
from ui import colors, fonts
from utils import tintar_icono


class MetadataFrame(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        self._ruta: str | None = None
        self._imagenes_lote: list[str] = []
        self._metadatos: dict[str, str] = {}
        self._preview_img: ctk.CTkImage | None = None
        self._thumbs: list[ctk.CTkImage] = []
        self._filas_lote: list[ctk.CTkLabel] = []
        self._campos_edit: dict[str, ctk.CTkEntry] = {}
        self._build()

    # ─── BUILD ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Título
        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=28, pady=(26, 8), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila_titulo,
            text='Metadatos EXIF',
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_limpiar_sel = ctk.CTkButton(
            fila_titulo,
            text='Limpiar',
            width=80, height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color='#FFFFFF',
            text_color='#1A1A1A',
            hover_color='#EEEEEE',
            border_width=0,
            command=self._limpiar_todo
        )
        self._btn_limpiar_sel.grid(row=0, column=1, sticky='e')

        # Tabs
        self._tab = ctk.CTkSegmentedButton(
            self,
            values=['Ver', 'Editar', 'Limpiar lote'],
            font=fonts.FUENTE_BASE,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.PANEL_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_tab
        )
        self._tab.set('Ver')
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 8), sticky='ew')

        # Contenedor de tabs
        self._contenedor = ctk.CTkFrame(self, fg_color='transparent')
        self._contenedor.grid(row=2, column=0, sticky='nsew')
        self._contenedor.grid_columnconfigure(0, weight=1)

        self._frames: dict[str, ctk.CTkFrame] = {}
        self._frames['Ver']          = self._build_tab_ver()
        self._frames['Editar']       = self._build_tab_editar()
        self._frames['Limpiar lote'] = self._build_tab_limpiar()

        for f in self._frames.values():
            f.grid(row=0, column=0, sticky='nsew')

        # Info
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=3, column=0, pady=(0, 4))

        self._cambiar_tab('Ver')

    # ─── TAB VER ──────────────────────────────────────────────────────────────

    def _build_tab_ver(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, 'Seleccionar imagen', self._explorar_ver)
        btn.grid(row=0, column=0, padx=28, pady=8, sticky='ew')
        self._dz_ver = btn

        # Panel de metadatos
        panel = ctk.CTkFrame(
            f, corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(0, weight=1)

        self._scroll_meta = ctk.CTkScrollableFrame(
            panel, fg_color='transparent',
            border_width=0, height=220
        )
        self._scroll_meta.grid(row=0, column=0, padx=8, pady=8, sticky='ew')
        self._scroll_meta.grid_columnconfigure(0, weight=1)
        self._scroll_meta.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._scroll_meta,
            text='Sin metadatos — cargá una imagen',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        # Botones exportar
        fila_exp = ctk.CTkFrame(panel, fg_color='transparent')
        fila_exp.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='ew')
        fila_exp.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            fila_exp,
            text='Exportar .txt',
            height=36, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=lambda: self._exportar('txt')
        ).grid(row=0, column=0, padx=(0, 6), sticky='ew')

        ctk.CTkButton(
            fila_exp,
            text='Exportar .json',
            height=36, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=lambda: self._exportar('json')
        ).grid(row=0, column=1, padx=(6, 0), sticky='ew')

        return f

    # ─── TAB EDITAR ───────────────────────────────────────────────────────────

    def _build_tab_editar(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, 'Seleccionar imagen', self._explorar_editar)
        btn.grid(row=0, column=0, padx=28, pady=8, sticky='ew')

        panel = ctk.CTkFrame(
            f, corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        for i, (campo, etiqueta) in enumerate(CAMPOS_EDITABLES.items()):
            ctk.CTkLabel(
                panel, text=etiqueta,
                font=fonts.FUENTE_BASE,
                text_color=colors.TEXT_GRAY, anchor='w'
            ).grid(row=i, column=0, padx=(16, 12), pady=8, sticky='w')

            entry = ctk.CTkEntry(
                panel,
                font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG,
                border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
                placeholder_text=f'Ingresá {etiqueta.lower()}...',
                placeholder_text_color=colors.TEXT_GRAY
            )
            entry.grid(row=i, column=1, padx=(0, 16), pady=8, sticky='ew')
            self._campos_edit[campo] = entry

        self._btn_guardar_edit = ctk.CTkButton(
            panel,
            text='Guardar cambios',
            height=40, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._guardar_edicion
        )
        self._btn_guardar_edit.grid(
            row=len(CAMPOS_EDITABLES), column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

        return f

    # ─── TAB LIMPIAR ──────────────────────────────────────────────────────────

    def _build_tab_limpiar(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, 'Seleccionar imágenes', self._explorar_lote)
        btn.grid(row=0, column=0, padx=28, pady=8, sticky='ew')

        self._lista_lote = ctk.CTkScrollableFrame(
            f, corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=0,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.ACENTO_DIMMED,
            height=160
        )
        self._lista_lote.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        self._lista_lote.grid_columnconfigure(0, weight=1)

        self._lbl_lote_vacio = ctk.CTkLabel(
            self._lista_lote,
            text='Sin imágenes cargadas',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_lote_vacio.pack(pady=12)

        panel_opc = ctk.CTkFrame(
            f, corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_opc.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        panel_opc.grid_columnconfigure(0, weight=1)

        self._btn_limpiar_exif = ctk.CTkButton(
            panel_opc,
            text='Limpiar EXIF',
            height=40, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._limpiar_lote
        )
        self._btn_limpiar_exif.grid(row=0, column=0, padx=16, pady=16, sticky='ew')

        return f

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    def _crear_boton_seleccionar(self, parent, texto: str, comando) -> ctk.CTkButton:
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

    def _renderizar_metadatos(self, metadatos: dict[str, str]):
        for w in self._scroll_meta.winfo_children():
            w.destroy()

        if not metadatos:
            ctk.CTkLabel(
                self._scroll_meta,
                text='Esta imagen no tiene metadatos EXIF',
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=0, columnspan=2, pady=20)
            return

        gps = metadatos.get('__gps_decimal__')

        for i, (k, v) in enumerate(metadatos.items()):
            if k.startswith('__'):
                continue

            ctk.CTkLabel(
                self._scroll_meta, text=k,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY, anchor='w'
            ).grid(row=i, column=0, padx=(8, 4), pady=3, sticky='w')

            # Si es GPS y hay coordenadas → link clickeable
            if 'GPS' in k and gps:
                url = f'https://maps.google.com/?q={gps}'
                lbl = ctk.CTkLabel(
                    self._scroll_meta, text=f'{v}  →  Ver en Maps',
                    font=fonts.FUENTE_CHICA,
                    text_color=colors.ACENTO, anchor='w',
                    cursor='hand2'
                )
                lbl.grid(row=i, column=1, padx=(4, 8), pady=3, sticky='w')
                lbl.bind('<Button-1>', lambda _, u=url: webbrowser.open(u))
            else:
                ctk.CTkLabel(
                    self._scroll_meta, text=v,
                    font=fonts.FUENTE_CHICA,
                    text_color=colors.TEXT_COLOR, anchor='w'
                ).grid(row=i, column=1, padx=(4, 8), pady=3, sticky='w')

    # ─── LÓGICA VER ───────────────────────────────────────────────────────────

    def _explorar_ver(self):
        archivo = filedialog.askopenfilename(
            title='Seleccioná una imagen',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.tiff *.webp')]
        )
        if not archivo:
            return
        self._ruta = archivo
        self._lbl_info.configure(text='Leyendo metadatos...')
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        meta = leer_metadatos(self._ruta)  # type: ignore
        self.after(0, lambda: self._aplicar_metadatos(meta))

    def _aplicar_metadatos(self, meta: dict[str, str]):
        self._metadatos = meta
        self._renderizar_metadatos(meta)
        n = len([k for k in meta if not k.startswith('__')])
        self._lbl_info.configure(
            text=f'{n} campos encontrados — {Path(self._ruta).name}' if self._ruta else ''
        )

    def _exportar(self, fmt: str):
        if not self._metadatos:
            self._lbl_info.configure(text='Primero cargá una imagen.')
            return
        ext = f'.{fmt}'
        ruta = filedialog.asksaveasfilename(
            title='Exportar metadatos',
            defaultextension=ext,
            filetypes=[(fmt.upper(), f'*{ext}')],
            initialfile=f'metadatos{ext}'
        )
        if not ruta:
            return
        if fmt == 'txt':
            exportar_txt(self._metadatos, ruta)
        else:
            exportar_json(self._metadatos, ruta)
        self._lbl_info.configure(text=f'Exportado como {Path(ruta).name}')

    # ─── LÓGICA EDITAR ────────────────────────────────────────────────────────

    def _explorar_editar(self):
        archivo = filedialog.askopenfilename(
            title='Seleccioná una imagen',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.tiff')]
        )
        if not archivo:
            return
        self._ruta = archivo
        # Precargar valores existentes
        meta = leer_metadatos(archivo)
        mapa_inv = {v: k for k, v in CAMPOS_EDITABLES.items()}
        for etiqueta, entry in zip(CAMPOS_EDITABLES.values(), self._campos_edit.values()):
            entry.delete(0, 'end')
            if etiqueta in meta:
                entry.insert(0, meta[etiqueta])
        self._lbl_info.configure(text=f'Editando: {Path(archivo).name}')

    def _guardar_edicion(self):
        if not self._ruta:
            self._lbl_info.configure(text='Primero cargá una imagen.')
            return

        campos = {
            campo: entry.get()
            for campo, entry in self._campos_edit.items()
            if entry.get().strip()
        }
        if not campos:
            self._lbl_info.configure(text='Ingresá al menos un campo para editar.')
            return

        ruta = filedialog.asksaveasfilename(
            title='Guardar imagen editada',
            defaultextension=Path(self._ruta).suffix,
            filetypes=[('JPEG', '*.jpg'), ('TIFF', '*.tiff')],
            initialfile=Path(self._ruta).stem + '_editado' + Path(self._ruta).suffix
        )
        if not ruta:
            return

        self._btn_guardar_edit.configure(state='disabled', text='Guardando...')

        def _proc():
            ok = editar_exif(self._ruta, ruta, campos)  # type: ignore
            self.after(0, lambda: self._btn_guardar_edit.configure(
                state='normal', text='Guardar cambios'
            ))
            msg = f'Guardado: {Path(ruta).name}' if ok else 'Error al guardar'
            self.after(0, lambda: self._lbl_info.configure(text=msg))

        threading.Thread(target=_proc, daemon=True).start()

    # ─── LÓGICA LIMPIAR LOTE ──────────────────────────────────────────────────

    def _explorar_lote(self):
        archivos = filedialog.askopenfilenames(
            title='Seleccioná imágenes',
            filetypes=[('Imágenes', '*.jpg *.jpeg *.png *.tiff *.webp')]
        )
        if archivos:
            self._cargar_lote(list(archivos))

    def _cargar_lote(self, rutas: list[str]):
        self._imagenes_lote = rutas
        self._thumbs.clear()
        self._filas_lote.clear()

        for w in self._lista_lote.winfo_children():
            w.destroy()

        for ruta in rutas:
            p = Path(ruta)
            fila = ctk.CTkFrame(
                self._lista_lote, fg_color=colors.SIDEBAR_BG, corner_radius=8
            )
            fila.pack(fill='x', pady=3, padx=2)
            fila.grid_columnconfigure(1, weight=1)

            lbl_thumb = ctk.CTkLabel(
                fila, text='', width=40, height=40, fg_color='transparent'
            )
            lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)
            self._filas_lote.append(lbl_thumb)

            info = ctk.CTkFrame(fila, fg_color='transparent')
            info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

            nombre = p.name if len(p.name) <= 32 else p.name[:29] + '...'
            ctk.CTkLabel(
                info, text=nombre,
                font=fonts.FUENTE_BASE,
                text_color=colors.TEXT_COLOR, anchor='w'
            ).pack(anchor='w')
            ctk.CTkLabel(
                info, text=formatear_bytes(p.stat().st_size),
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY, anchor='w'
            ).pack(anchor='w')

        threading.Thread(
            target=self._cargar_thumbs_lote, args=(rutas,), daemon=True
        ).start()
        n = len(rutas)
        self._lbl_info.configure(
            text=f'{n} imagen{"es" if n > 1 else ""} listas para limpiar'
        )

    def _cargar_thumbs_lote(self, rutas: list[str]):
        thumbs = []
        for ruta in rutas:
            try:
                img = Image.open(ruta)
                img.thumbnail((40, 40), Image.Resampling.LANCZOS)
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
            except Exception:
                thumb = None
            thumbs.append(thumb)
        self.after(0, lambda: self._aplicar_thumbs(thumbs))

    def _aplicar_thumbs(self, thumbs):
        for i, thumb in enumerate(thumbs):
            if thumb and i < len(self._filas_lote):
                self._filas_lote[i].configure(image=thumb)
        self._thumbs = [t for t in thumbs if t]

    def _limpiar_lote(self):
        if not self._imagenes_lote:
            self._lbl_info.configure(text='Primero cargá imágenes.')
            return
        carpeta = filedialog.askdirectory(title='Carpeta de salida')
        if not carpeta:
            return
        self._btn_limpiar_exif.configure(state='disabled', text='Limpiando...')
        threading.Thread(
            target=self._proceso_limpiar, args=(carpeta,), daemon=True
        ).start()

    def _proceso_limpiar(self, carpeta: str):
        errores = 0
        for ruta in self._imagenes_lote:
            try:
                p = Path(ruta)
                salida = str(Path(carpeta) / (p.stem + '_sinexif' + p.suffix))
                limpiar_exif(ruta, salida)
            except Exception:
                errores += 1
        n = len(self._imagenes_lote)
        ok = n - errores
        self.after(0, lambda: self._btn_limpiar_exif.configure(
            state='normal', text='Limpiar EXIF'
        ))
        msg = f'{ok} imagen{"es" if ok != 1 else ""} limpiadas'
        if errores:
            msg += f'  ·  {errores} con error'
        self.after(0, lambda: self._lbl_info.configure(text=msg))

    # ─── CAMBIO DE TAB ────────────────────────────────────────────────────────

    def _cambiar_tab(self, tab: str):
        for nombre, frame in self._frames.items():
            if nombre == tab:
                frame.tkraise()
            
    def _limpiar_todo(self):
        self._ruta = None
        self._imagenes_lote = []
        self._metadatos = {}
        self._thumbs.clear()
        self._filas_lote.clear()

        for w in self._scroll_meta.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._scroll_meta,
            text='Sin metadatos — cargá una imagen',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        for entry in self._campos_edit.values():
            entry.delete(0, 'end')

        for w in self._lista_lote.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._lista_lote,
            text='Sin imágenes cargadas',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=12)

        self._lbl_info.configure(text='')