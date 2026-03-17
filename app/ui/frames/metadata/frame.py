"""
UI para el modulo Metadatos EXIF.
Tabs: Ver - Editar - Limpiar
"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog
import webbrowser

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.utils import tintar_icono
from app.ui.file_list import build_file_list, load_thumbs_async
from app.ui.frames.base import BaseFrame
from app.ui.frames.metadata.services import (
    leer_metadatos_safe,
    editar_exif,
    exportar_metadatos,
    preparar_campos_exif,
    CAMPOS_EDITABLES,
    batch_limpiar_exif,
)
from app.ui.frames.metadata.state import MetadataState


class MetadataFrame(BaseFrame):
    def __init__(self, parent):
        self._state = MetadataState()
        self._preview_img: ctk.CTkImage | None = None
        self._thumbs: list[ctk.CTkImage] = []
        self._filas_lote: list[ctk.CTkLabel] = []
        self._campos_edit: dict[str, ctk.CTkEntry] = {}
        super().__init__(parent, t('metadata_title'))

    def _build_content(self):
        self.grid_columnconfigure(0, weight=1)
        # Tabs
        self._tab = ctk.CTkSegmentedButton(
            self,
            values=[t('view'), t('edit'), t('clean_batch')],
            font=fonts.FUENTE_BASE,
            selected_color='#949494',
            selected_hover_color='#949494',
            unselected_color=colors.PANEL_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_tab
        )
        self._tab.set(t('view'))
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 8), sticky='ew')

        # Contenedor de tabs
        self._contenedor = ctk.CTkFrame(self, fg_color='transparent')
        self._contenedor.grid(row=2, column=0, sticky='nsew')
        self._contenedor.grid_columnconfigure(0, weight=1)

        self._frames: dict[str, ctk.CTkFrame] = {}
        self._frames[t('view')] = self._build_tab_ver()
        self._frames[t('edit')] = self._build_tab_editar()
        self._frames[t('clean_batch')] = self._build_tab_limpiar()

        for f in self._frames.values():
            f.grid(row=0, column=0, sticky='nsew')

        self._cambiar_tab(t('view'))

    def _build_tab_ver(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, t('select_image_view'), self._explorar_ver)
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
            text=t('no_metadata'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        # Botones exportar
        fila_exp = ctk.CTkFrame(panel, fg_color='transparent')
        fila_exp.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='ew')
        fila_exp.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            fila_exp,
            text=t('export_txt'),
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
            text=t('export_json'),
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

    def _build_tab_editar(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, t('select_image_edit'), self._explorar_editar)
        btn.grid(row=0, column=0, padx=28, pady=8, sticky='ew')

        panel = ctk.CTkFrame(
            f, corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        _label_map = {
            'Artist': 'artist',
            'Copyright': 'copyright',
            'Software': 'software',
            'DateTime': 'datetime',
        }
        for i, (campo, etiqueta) in enumerate(CAMPOS_EDITABLES.items()):
            etiqueta_trad = t(_label_map.get(campo, '')) if campo in _label_map else etiqueta
            ctk.CTkLabel(
                panel, text=etiqueta_trad,
                font=fonts.FUENTE_BASE,
                text_color=colors.TEXT_GRAY, anchor='w'
            ).grid(row=i, column=0, padx=(16, 12), pady=8, sticky='w')

            entry = ctk.CTkEntry(
                panel,
                font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG,
                border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
                placeholder_text=t('enter_field').format(etiqueta_trad.lower()),
                placeholder_text_color=colors.TEXT_GRAY
            )
            entry.grid(row=i, column=1, padx=(0, 16), pady=8, sticky='ew')
            self._campos_edit[campo] = entry

        self._btn_guardar_edit = ctk.CTkButton(
            panel,
            text=t('save_changes'),
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

    def _build_tab_limpiar(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        btn = self._crear_boton_seleccionar(f, t('select_images_clean'), self._explorar_lote)
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
            text=t('no_images'),
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
            text=t('clean_exif'),
            height=40, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._limpiar_lote
        )
        self._btn_limpiar_exif.grid(row=0, column=0, padx=16, pady=16, sticky='ew')

        return f

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
                text=t('no_metadata_image'),
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

            # Si es GPS y hay coordenadas -> link clickeable
            if 'GPS' in k and gps:
                url = f'https://maps.google.com/?q={gps}'
                lbl = ctk.CTkLabel(
                    self._scroll_meta, text=f'{v}  ->  {t("view_on_maps")}',
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

    def _explorar_ver(self):
        archivo = filedialog.askopenfilename(
            title=t('select_image_view'),
            filetypes=[('Imagenes', '*.jpg *.jpeg *.png *.tiff *.webp')]
        )
        if not archivo:
            return
        self._state.ruta = archivo
        self._lbl_info.configure(text=t('reading_metadata'))
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        meta, err = leer_metadatos_safe(self._state.ruta)  # type: ignore
        if err:
            self.after(0, lambda: self._lbl_info.configure(text=f'{t("error_generic")}: {err}'))
            return
        self.after(0, lambda: self._aplicar_metadatos(meta))

    def _aplicar_metadatos(self, meta: dict[str, str]):
        self._state.metadatos = meta
        self._renderizar_metadatos(meta)
        n = len([k for k in meta if not k.startswith('__')])
        self._lbl_info.configure(
            text=f'{n} {t("fields_found")} - {Path(self._state.ruta).name}' if self._state.ruta else ''
        )

    def _exportar(self, fmt: str):
        if not self._state.metadatos:
            self._lbl_info.configure(text=t('export_metadata_first'))
            return
        ext = f'.{fmt}'
        ruta = filedialog.asksaveasfilename(
            title=t('export_metadata'),
            defaultextension=ext,
            filetypes=[(fmt.upper(), f'*{ext}')],
            initialfile=f'metadatos{ext}'
        )
        if not ruta:
            return
        exportar_metadatos(self._state.metadatos, ruta, fmt)
        self._lbl_info.configure(text=f'{t("exported_as")} {Path(ruta).name}')

    def _explorar_editar(self):
        archivo = filedialog.askopenfilename(
            title=t('select_image_edit'),
            filetypes=[('Imagenes', '*.jpg *.jpeg *.tiff')]
        )
        if not archivo:
            return
        self._state.ruta = archivo
        # Precargar valores existentes
        meta, _ = leer_metadatos_safe(archivo)
        for etiqueta, entry in zip(CAMPOS_EDITABLES.values(), self._campos_edit.values()):
            entry.delete(0, 'end')
            if etiqueta in meta:
                entry.insert(0, meta[etiqueta])
        self._lbl_info.configure(text=f'{t("editing")} {Path(archivo).name}')

    def _guardar_edicion(self):
        if not self._state.ruta:
            self._lbl_info.configure(text=t('export_metadata_first'))
            return

        campos_raw = {campo: entry.get() for campo, entry in self._campos_edit.items()}
        campos, err = preparar_campos_exif(campos_raw)
        if err:
            self._lbl_info.configure(text=t('enter_at_least_one'))
            return

        ruta = filedialog.asksaveasfilename(
            title=t('select_output_save'),
            defaultextension=Path(self._state.ruta).suffix,
            filetypes=[('JPEG', '*.jpg'), ('TIFF', '*.tiff')],
            initialfile=Path(self._state.ruta).stem + '_editado' + Path(self._state.ruta).suffix
        )
        if not ruta:
            return

        self._btn_guardar_edit.configure(state='disabled', text=t('saving_changes'))

        def _proc():
            ok = editar_exif(self._state.ruta, ruta, campos)  # type: ignore
            self.after(0, lambda: self._btn_guardar_edit.configure(
                state='normal', text=t('save_changes')
            ))
            msg = f'{t("saved_as_file")} {Path(ruta).name}' if ok else t('error_saving')
            self.after(0, lambda: self._lbl_info.configure(text=msg))

        threading.Thread(target=_proc, daemon=True).start()

    def _explorar_lote(self):
        archivos = filedialog.askopenfilenames(
            title=t('select_images_clean'),
            filetypes=[('Imagenes', '*.jpg *.jpeg *.png *.tiff *.webp')]
        )
        if archivos:
            self._cargar_lote(list(archivos))

    def _cargar_lote(self, rutas: list[str]):
        self._state.imagenes_lote = rutas
        build_file_list(
            self._lista_lote, rutas, self._filas_lote, self._thumbs,
            thumb_size=40, show_ext=False
        )
        load_thumbs_async(rutas, self._filas_lote, self._thumbs, self.after, thumb_size=40)
        n = len(rutas)
        self._lbl_info.configure(
            text=f'{n} {t("images_ready_clean")}'
        )

    def _limpiar_lote(self):
        if not self._state.imagenes_lote:
            self._lbl_info.configure(text=t('load_images_first_clean'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder_clean'))
        if not carpeta:
            return
        self._btn_limpiar_exif.configure(state='disabled', text=t('cleaning'))
        threading.Thread(
            target=self._proceso_limpiar, args=(carpeta,), daemon=True
        ).start()

    def _proceso_limpiar(self, carpeta: str):
        res = batch_limpiar_exif(self._state.imagenes_lote, carpeta)
        self.after(0, lambda: self._btn_limpiar_exif.configure(
            state='normal', text=t('clean_exif')
        ))
        msg = f'{res["ok"]} {t("cleaned")}'
        if res['errores']:
            msg += f'  -  {res["errores"]} {t("error_occurred")}'
        self.after(0, lambda: self._lbl_info.configure(text=msg))

    def _cambiar_tab(self, tab: str):
        for nombre, frame in self._frames.items():
            if nombre == tab:
                frame.tkraise()

    def _limpiar(self):
        self._limpiar_todo()

    def _limpiar_todo(self):
        self._state.ruta = None
        self._state.imagenes_lote = []
        self._state.metadatos = {}
        self._thumbs.clear()
        self._filas_lote.clear()

        for w in self._scroll_meta.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._scroll_meta,
            text=t('no_metadata'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        for entry in self._campos_edit.values():
            entry.delete(0, 'end')

        for w in self._lista_lote.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._lista_lote,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=12)

        self._lbl_info.configure(text='')
