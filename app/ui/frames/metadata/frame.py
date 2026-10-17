"""Interfaz grafica para gestionar metadatos EXIF de imagenes.

Permite:
    - Ver: Leer y visualizar metadatos de una imagen
    - Editar: Modificar campos editables (autor, copyright, software, fecha)
    - Limpiar: Eliminar todos los metadatos EXIF de multiples imagenes

Relaciones:
    - BaseFrame: app.ui.frames.base.BaseFrame
    - Traducciones: app.translations
    - Colores: app.ui.colors
    - Fuentes: app.ui.fonts
    - Utilidades: app.utils (tintar_icono)
    - Lista de archivos: app.ui.file_list
    - Servicios: app.ui.frames.metadata.services
    - Estado: app.ui.frames.metadata.state
"""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox
import webbrowser

import customtkinter as ctk
from PIL import Image, ImageOps

from app.ui import colors, fonts
from app.ui.scale import scale_wraplength
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
    GRUPOS_CAMPOS_EDITABLES,
    CAMPOS_VISIBLES,
    GRUPOS_CAMPOS_VISIBLES,
    OPCIONES_ENUM_EXIF as _ENUM_OPTIONS,
    ORIENTACIONES_EXIF as _ORIENTATION_OPTIONS,
    leer_campos_edicion_safe,
    batch_limpiar_exif,
)
from app.ui.frames.metadata.state import MetadataState


logger = logging.getLogger(__name__)


def _cargar_preview_edicion(ruta: str) -> Image.Image:
    """Decodifica una copia acotada para visualizar, sin modificar el archivo."""
    with Image.open(ruta) as imagen:
        imagen.draft('RGB', (1024, 1024))
        preview = ImageOps.exif_transpose(imagen)
        preview.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        return preview.convert('RGB')


class MetadataFrame(BaseFrame):
    """Frame principal del modulo de gestion de metadatos EXIF."""

    def __init__(self, parent):
        logger.info("metadata.ui: init")
        self._state = MetadataState()
        self._preview_img: ctk.CTkImage | None = None
        self._edit_preview_source: Image.Image | None = None
        self._edit_preview_job = None
        self._edit_preview_size = None
        self._metadata_rows = []
        self._metadata_sections = []
        self._thumbs: list[ctk.CTkImage] = []
        self._filas_lote: list[ctk.CTkLabel] = []
        self._campos_edit: dict[str, ctk.CTkEntry | ctk.CTkComboBox] = {}
        self._enum_values: dict[str, dict[str, str]] = {}
        self._orientacion_values: dict[str, int] = {}
        super().__init__(parent, t('metadata_title'))

    def _build_content(self):
        """Construir el contenido principal con tabs Ver, Editar y Limpiar."""
        logger.info("metadata.ui: build_content")
        self.grid_columnconfigure(0, weight=1)

        self._tab = ctk.CTkSegmentedButton(
            self,
            values=[t('view'), t('edit'), t('clean_batch')],
            font=fonts.FUENTE_BASE,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.PANEL_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_tab
        )
        self._tab.set(t('view'))
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 8), sticky='ew')

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
        """Construir el tab de visualizacion de metadatos."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        izquierda, derecha = self._crear_workspace(f, row=0, breakpoint=720, padx=16, pady=0)
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(1, weight=1)

        btn = self._crear_boton_seleccionar(izquierda, t('select_image_view'), self._explorar_ver)
        btn.grid(row=0, column=0, padx=16, pady=16, sticky='ew')
        self._dz_ver = btn

        ctk.CTkLabel(
            izquierda, text=t('select_image_view'), font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, justify='left', wraplength=300,
        ).grid(row=1, column=0, padx=16, pady=(0, 16), sticky='nw')

        panel = derecha
        panel.grid_columnconfigure(0, weight=1)

        self._scroll_meta = ctk.CTkScrollableFrame(
            panel, fg_color='transparent',
            border_width=0, height=320
        )
        self._scroll_meta.grid(row=1, column=0, padx=16, pady=8, sticky='nsew')
        self._scroll_meta.grid_columnconfigure(0, weight=2, uniform='metadata-columns')
        self._scroll_meta.grid_columnconfigure(1, weight=3, uniform='metadata-columns')
        self._scroll_meta.bind('<Configure>', self._ajustar_filas_metadatos, add='+')

        ctk.CTkLabel(
            self._scroll_meta,
            text=t('no_metadata'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        ctk.CTkLabel(
            panel, text=t('metadata_title'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(16, 0), sticky='w')

        fila_exp = ctk.CTkFrame(panel, fg_color='transparent')
        fila_exp.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='ew')
        fila_exp.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            fila_exp,
            text=t('export_txt'),
            height=36, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=lambda: self._exportar('txt')
        ).grid(row=0, column=0, padx=(0, 6), sticky='ew')

        ctk.CTkButton(
            fila_exp,
            text=t('export_json'),
            height=36, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=lambda: self._exportar('json')
        ).grid(row=0, column=1, padx=(6, 0), sticky='ew')

        return f

    def _build_tab_editar(self) -> ctk.CTkFrame:
        """Construir el tab de edicion de metadatos."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        izquierda, derecha = self._crear_workspace(f, row=0, breakpoint=720, padx=16, pady=0)

        btn = self._crear_boton_seleccionar(izquierda, t('select_image_edit'), self._explorar_editar)
        btn.grid(row=0, column=0, padx=16, pady=16, sticky='ew')

        panel = ctk.CTkScrollableFrame(
            izquierda, corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            height=420,
        )
        self._panel_editar = panel
        panel.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='new')
        panel.grid_columnconfigure(1, weight=1)

        fila = 0
        for grupo, campos in GRUPOS_CAMPOS_EDITABLES.items():
            ctk.CTkLabel(
                panel, text=t(f'metadata_section_{grupo}'),
                font=fonts.FUENTE_TITULO, text_color=colors.TEXT_COLOR,
                anchor='w'
            ).grid(row=fila, column=0, columnspan=2, padx=16, pady=(14, 4), sticky='ew')
            fila += 1
            for campo in campos:
                fila = self._agregar_campo_edicion(panel, campo, fila)
            if grupo == 'gps':
                self._clear_gps_var = ctk.BooleanVar(value=False)
                ctk.CTkCheckBox(
                    panel, text=t('clear_gps'), variable=self._clear_gps_var,
                    font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR,
                ).grid(row=fila, column=0, columnspan=2, padx=16, pady=6, sticky='w')
                fila += 1

        ctk.CTkLabel(
            panel, text=t('metadata_section_dates'),
            font=fonts.FUENTE_TITULO, text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=fila, column=0, columnspan=2, padx=16, pady=(14, 4), sticky='ew')
        fila += 1
        fila = self._agregar_campo_edicion(panel, 'DateTimeOriginal', fila)
        self._sync_dates_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            panel, text=t('sync_dates'), variable=self._sync_dates_var,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR,
        ).grid(row=fila, column=0, columnspan=2, padx=16, pady=6, sticky='w')
        fila += 1

        ctk.CTkLabel(
            panel, text=t('metadata_section_orientation'),
            font=fonts.FUENTE_TITULO, text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=fila, column=0, columnspan=2, padx=16, pady=(14, 4), sticky='ew')
        fila += 1
        ctk.CTkLabel(
            panel, text=t('orientation_transform'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=fila, column=0, padx=(16, 12), pady=6, sticky='w')
        self._combo_orientacion = ctk.CTkComboBox(
            panel, values=[t('keep_orientation')] + [t(key) for key in _ORIENTATION_OPTIONS.values()],
            state='readonly', font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
        )
        self._combo_orientacion.set(t('keep_orientation'))
        self._orientacion_values = {t(key): value for value, key in _ORIENTATION_OPTIONS.items()}
        self._combo_orientacion.grid(row=fila, column=1, padx=(0, 16), pady=6, sticky='ew')
        fila += 1
        self._info_tecnica = ctk.CTkLabel(
            panel, text='', font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w', justify='left'
        )
        self._info_tecnica.grid(row=fila, column=0, columnspan=2, padx=16, pady=6, sticky='ew')
        fila += 1

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
            row=fila, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

        self._lbl_edit_target = ctk.CTkLabel(
            derecha, text=t('select_image_edit'),
            font=fonts.FUENTE_BASE, text_color=colors.TEXT_GRAY,
            justify='left', wraplength=scale_wraplength(360),
        )
        self._lbl_edit_target.grid(row=0, column=0, padx=16, pady=16, sticky='nw')

        derecha.grid_rowconfigure(1, weight=1)
        self._lbl_edit_preview = ctk.CTkLabel(
            derecha, text='', width=1, height=360,
            fg_color=colors.DROPZONE_BG, corner_radius=8,
        )
        self._lbl_edit_preview.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='nsew')
        self._lbl_edit_preview.bind('<Configure>', self._programar_preview_edicion, add='+')

        return f

    def _programar_preview_edicion(self, _event=None):
        """Agrupa los cambios de tamaño antes de ajustar la imagen al panel."""
        if self._edit_preview_job is None:
            self._edit_preview_job = self.after_idle(self._render_preview_edicion)

    def _render_preview_edicion(self):
        self._edit_preview_job = None
        source = self._edit_preview_source
        if source is None:
            self._lbl_edit_preview.configure(image=None)
            # CTkLabel no elimina la imagen nativa al recibir image=None.
            self._lbl_edit_preview._label.configure(image='')
            self._preview_img = None
            self._edit_preview_size = None
            return
        scale = self._get_widget_scaling()
        width = max(1, int(self._lbl_edit_preview.winfo_width() / scale) - 24)
        height = max(1, int(self._lbl_edit_preview.winfo_height() / scale) - 24)
        size = (id(source), width, height)
        if size == self._edit_preview_size:
            return
        preview = source.copy()
        preview.thumbnail((width, height), Image.Resampling.LANCZOS)
        image = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
        self._lbl_edit_preview.configure(image=image)
        self._preview_img = image
        self._edit_preview_size = size

    def _agregar_campo_edicion(self, panel, campo: str, fila: int) -> int:
        etiqueta = t(CAMPOS_EDITABLES[campo])
        ctk.CTkLabel(
            panel, text=etiqueta, font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=fila, column=0, padx=(16, 12), pady=6, sticky='w')

        if campo in _ENUM_OPTIONS:
            opciones = {t(clave): str(valor) for valor, clave in _ENUM_OPTIONS[campo].items()}
            self._enum_values[campo] = opciones
            widget = ctk.CTkComboBox(
                panel, values=[t('leave_unchanged')] + list(opciones),
                state='readonly', font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
            )
            widget.set(t('leave_unchanged'))
        else:
            placeholder = t('datetime_format_placeholder') if campo == 'DateTimeOriginal' else t('enter_field').format(etiqueta.lower())
            widget = ctk.CTkEntry(
                panel, font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR, placeholder_text=placeholder,
                placeholder_text_color=colors.TEXT_GRAY,
            )
        widget.grid(row=fila, column=1, padx=(0, 16), pady=6, sticky='ew')
        self._campos_edit[campo] = widget
        return fila + 1

    def _build_tab_limpiar(self) -> ctk.CTkFrame:
        """Construir el tab de limpieza de metadatos en lote."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        izquierda, derecha = self._crear_workspace(f, row=0, breakpoint=720, padx=16, pady=0)

        btn = self._crear_boton_seleccionar(izquierda, t('select_images_clean'), self._explorar_lote)
        btn.grid(row=0, column=0, padx=16, pady=16, sticky='ew')

        self._lista_lote = ctk.CTkScrollableFrame(
            derecha, corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=0,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.ACENTO_DIMMED,
            height=420
        )
        self._lista_lote.grid(row=0, column=0, padx=16, pady=16, sticky='nsew')
        self._lista_lote.grid_columnconfigure(0, weight=1)

        self._lbl_lote_vacio = ctk.CTkLabel(
            self._lista_lote,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_lote_vacio.pack(pady=12)

        self._btn_limpiar_exif = ctk.CTkButton(
            izquierda,
            text=t('clean_exif'),
            height=40, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._limpiar_lote
        )
        self._btn_limpiar_exif.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='ew')

        return f

    def _crear_boton_seleccionar(self, parent, texto: str, comando) -> ctk.CTkButton:
        """Crear boton de seleccion con icono.

        Args:
            parent: Widget padre
            texto: Texto del boton
            comando: Funcion de callback

        Returns:
            Boton CTk configurado
        """
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

    def _valor_metadato_visible(self, nombre: str, valor: str) -> str:
        """Traduce las opciones conocidas; conserva el código del archivo."""
        try:
            codigo = int(valor)
        except ValueError:
            return valor
        clave = None
        if nombre in _ENUM_OPTIONS:
            clave = _ENUM_OPTIONS[nombre].get(codigo)
            if nombre == 'Flash':
                clave = _ENUM_OPTIONS[nombre].get(codigo & 1)
        elif nombre == 'Orientation':
            clave = _ORIENTATION_OPTIONS.get(codigo)
        elif nombre == 'ColorSpace':
            clave = {1: 'color_srgb', 65535: 'color_uncalibrated'}.get(codigo)
        return f'{t(clave)} ({valor})' if clave else valor

    def _ajustar_filas_metadatos(self, _event=None):
        """Reparte el ancho entre campo y valor, permitiendo varias líneas."""
        ancho = max(160, int(self._scroll_meta.winfo_width() / self._get_widget_scaling()) - 32)
        for _, etiqueta, valor in self._metadata_rows:
            etiqueta.configure(wraplength=max(60, int(ancho * .4) - 12))
            valor.configure(wraplength=max(80, int(ancho * .6) - 12))
        for seccion in self._metadata_sections:
            seccion.configure(wraplength=ancho)

    def _renderizar_metadatos(self, metadatos: dict[str, str]):
        """Presenta campos conocidos por secciones, sin contenedores extra."""
        self._metadata_rows.clear()
        self._metadata_sections.clear()
        for widget in self._scroll_meta.winfo_children():
            widget.destroy()
        fila = 0
        gps = metadatos.get('__gps_decimal__')
        for grupo, nombres in GRUPOS_CAMPOS_VISIBLES.items():
            campos = [
                nombre for nombre in nombres
                if CAMPOS_VISIBLES[nombre][0] in metadatos
                and metadatos[CAMPOS_VISIBLES[nombre][0]].strip()
            ]
            if not campos:
                continue
            seccion = ctk.CTkLabel(
                self._scroll_meta, text=t(f'metadata_section_{grupo}'),
                font=fonts.FUENTE_BASE, text_color=colors.TEXT_COLOR,
                anchor='w', justify='left',
            )
            seccion.grid(row=fila, column=0, columnspan=2, padx=8, pady=(12 if fila else 4, 6), sticky='ew')
            self._metadata_sections.append(seccion)
            fila += 1
            for nombre in campos:
                clave, traduccion = CAMPOS_VISIBLES[nombre]
                etiqueta = ctk.CTkLabel(
                    self._scroll_meta, text=t(traduccion),
                    font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
                    anchor='nw', justify='left',
                )
                etiqueta.grid(row=fila, column=0, padx=(8, 4), pady=4, sticky='new')
                texto = self._valor_metadato_visible(nombre, metadatos[clave])
                es_mapa = nombre in ('GPSLatitude', 'GPSLongitude') and bool(gps)
                if es_mapa:
                    texto += f'  →  {t("view_on_maps")}'
                valor = ctk.CTkLabel(
                    self._scroll_meta, text=texto, font=fonts.FUENTE_CHICA,
                    text_color=colors.ACENTO if es_mapa else colors.TEXT_COLOR,
                    anchor='nw', justify='left',
                )
                valor.grid(row=fila, column=1, padx=(4, 8), pady=4, sticky='new')
                if es_mapa:
                    valor.configure(cursor='hand2')
                    url = f'https://maps.google.com/?q={gps}'
                    valor.bind('<Button-1>', lambda _, u=url: webbrowser.open(u))
                self._metadata_rows.append((nombre, etiqueta, valor))
                fila += 1
        if not self._metadata_rows:
            ctk.CTkLabel(
                self._scroll_meta, text=t('no_metadata_image'),
                font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            ).grid(row=0, column=0, columnspan=2, pady=20)
        self._ajustar_filas_metadatos()

    def _explorar_ver(self):
        """Abrir dialogo para seleccionar imagen y leer sus metadatos."""
        if self._operation_blocked(global_job=True):
            return
        logger.info("metadata.ui: explorar_ver")
        archivo = filedialog.askopenfilename(
            title=t('select_image_view'),
            filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.tiff *.webp *.heic *.heif')]
        )
        if not archivo:
            return
        self._state.ruta = archivo
        self._lbl_info.configure(text=t('reading_metadata'))
        self._show_full_overlay(t('processing'))
        self._submit_job(lambda: self._leer(archivo))

    def _leer(self, archivo):
        """Leer metadatos en hilo separado."""
        meta, err = leer_metadatos_safe(archivo)  # type: ignore
        if err:
            self._post_ui(0, self._hide_full_overlay)
            self._post_ui(0, lambda: self._lbl_info.configure(text=f'{t("error_generic")}: {err}'))
            return
        self._post_ui(0, lambda: self._aplicar_metadatos(meta))

    def _aplicar_metadatos(self, meta: dict[str, str]):
        """Aplicar metadatos leidos a la interfaz.

        Args:
            meta: Diccionario con los metadatos leidos
        """
        self._state.metadatos = meta
        self._renderizar_metadatos(meta)
        self._hide_full_overlay()
        n = len([k for k in meta if not k.startswith('__')])
        self._lbl_info.configure(
            text=f'{n} {t("fields_found")} - {Path(self._state.ruta).name}' if self._state.ruta else ''
        )

    def _exportar(self, fmt: str):
        """Exportar metadatos al formato seleccionado.

        Args:
            fmt: Formato de exportacion ('txt' o 'json')
        """
        if self._operation_blocked(global_job=True):
            return
        logger.info("metadata.ui: exportar (fmt=%s)", fmt)
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
        try:
            exportar_metadatos(self._state.metadatos, ruta, fmt)
        except Exception:
            logger.exception('Metadata export failed')
            self._lbl_info.configure(text=t('error_saving'))
            return
        self._lbl_info.configure(text=f'{t("exported_as")} {Path(ruta).name}')

    def _explorar_editar(self):
        """Abrir dialogo para seleccionar imagen y precargar campos editables."""
        if self._operation_blocked(global_job=True):
            return
        logger.info("metadata.ui: explorar_editar")
        archivo = filedialog.askopenfilename(
            title=t('select_image_edit'),
            filetypes=[('JPEG / TIFF', '*.jpg *.jpeg *.tif *.tiff')]
        )
        if not archivo:
            return
        self._lbl_info.configure(text=t('reading_metadata'))
        self._show_full_overlay(t('processing'))

        def _proc():
            meta, error = leer_campos_edicion_safe(archivo)
            if error:
                raise ValueError(error)
            return meta, _cargar_preview_edicion(archivo)

        def loaded(result):
            meta, preview = result
            self._state.ruta_edicion = archivo
            self._edit_preview_source = preview
            self._programar_preview_edicion()
            self._aplicar_campos_edit(meta)

        self._submit_job(_proc, on_success=loaded)

    def _aplicar_campos_edit(self, meta: dict):
        """Aplicar metadatos a los campos editables."""
        for campo, widget in self._campos_edit.items():
            valor = meta.get(campo, '')
            if isinstance(widget, ctk.CTkComboBox):
                display = next(
                    (label for label, code in self._enum_values[campo].items() if code == str(valor)),
                    t('leave_unchanged'),
                )
                widget.set(display)
            else:
                widget.delete(0, 'end')
                if valor:
                    widget.insert(0, valor)
        self._loaded_edit_values = {key: (self._enum_values[key].get(widget.get(), '') if key in self._enum_values else widget.get().strip()) for key, widget in self._campos_edit.items()}
        self._sync_dates_var.set(False)
        self._clear_gps_var.set(False)
        self._combo_orientacion.set(t('keep_orientation'))
        orientation_key = _ORIENTATION_OPTIONS.get(int(meta.get('__orientation__', 1)), 'orient_normal')
        color_space = meta.get('__color_space__', '')
        if color_space == '1':
            color_space = t('color_srgb')
        elif color_space == '65535':
            color_space = t('color_uncalibrated')
        elif not color_space:
            color_space = t('unknown')
        self._info_tecnica.configure(text=(
            f"{t('current_orientation')}: {t(orientation_key)}  |  "
            f"{t('dimensions')}: {meta.get('__image_size__', t('unknown'))}  |  "
            f"{t('color_space')}: {color_space}"
        ))
        if self._state.ruta_edicion:
            self._lbl_info.configure(text=f'{t("editing")} {Path(self._state.ruta_edicion).name}')
            if hasattr(self, '_lbl_edit_target'):
                self._lbl_edit_target.configure(text=f'{t("editing")}\n{Path(self._state.ruta_edicion).name}')
        self._hide_full_overlay()

    def _guardar_edicion(self):
        """Guardar los cambios de metadatos editados."""
        if self._operation_blocked(global_job=True):
            return
        logger.info("metadata.ui: guardar_edicion")
        if not self._state.ruta_edicion:
            self._lbl_info.configure(text=t('export_metadata_first'))
            return

        campos_raw = {}
        for campo, widget in self._campos_edit.items():
            valor = widget.get().strip()
            if campo in self._enum_values:
                valor = self._enum_values[campo].get(valor, '')
            campos_raw[campo] = valor
        original = getattr(self, '_loaded_edit_values', {})
        changed = {key: value for key, value in campos_raw.items() if value and value != original.get(key, '')}
        if self._sync_dates_var.get() and campos_raw.get('DateTimeOriginal'):
            changed['DateTimeOriginal'] = campos_raw['DateTimeOriginal']
        gps_keys = ('GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection')
        if any(key in changed for key in gps_keys):
            for key in gps_keys:
                if campos_raw.get(key):
                    changed[key] = campos_raw[key]
        campos_raw = changed
        if self._clear_gps_var.get():
            for key in ('GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSImgDirection'):
                campos_raw.pop(key, None)
        orientacion = self._orientacion_values.get(self._combo_orientacion.get())
        campos, err = preparar_campos_exif(
            campos_raw,
            sync_dates=self._sync_dates_var.get(),
            clear_gps=self._clear_gps_var.get(),
            orientation=orientacion,
        )
        if err:
            mensajes = {
                'invalid_date': 'invalid_date_format',
                'invalid_number': 'invalid_metadata_number',
                'invalid_option': 'invalid_metadata_option',
                'invalid_gps': 'invalid_gps',
                'gps_pair': 'gps_pair_required',
                'gps_conflict': 'gps_clear_conflict',
                'sync_requires_date': 'sync_date_required',
                'invalid_orientation': 'invalid_orientation',
                'empty': 'no_metadata_changes',
            }
            self._lbl_info.configure(text=t(mensajes.get(err, 'error_saving')))
            return

        confirm = messagebox.askyesno(
            title=t('confirm_overwrite_title'),
            message=t('confirm_overwrite_msg')
        )
        if not confirm:
            return
        ruta = self._state.ruta_edicion

        self._btn_guardar_edit.configure(state='disabled', text=t('saving_changes'))

        def _proc():
            ok, warning = editar_exif(ruta, ruta, campos)  # type: ignore
            self._post_ui(0, lambda: self._btn_guardar_edit.configure(
                state='normal', text=t('save_changes')
            ))
            if ok:
                try:
                    preview = _cargar_preview_edicion(ruta)
                except Exception:
                    logger.warning('No se pudo actualizar la preview de %s', ruta, exc_info=True)
                else:
                    def actualizar_preview():
                        self._edit_preview_source = preview
                        self._programar_preview_edicion()
                    self._post_ui(0, actualizar_preview)
                msg = f'{t("saved_as_file")} {Path(ruta).name}'
                if warning == 'no_exif':
                    msg += f'  -  {t("saved_without_exif")}'
            else:
                msg = t('unsupported_frames') if warning == 'unsupported_frames' else t('error_saving')
            self._post_ui(0, lambda: self._lbl_info.configure(text=msg))

        self._submit_job(_proc, button=self._btn_guardar_edit, text=t('save_changes'))

    def _explorar_lote(self):
        """Abrir dialogo para seleccionar multiples imagenes a limpiar."""
        if self._operation_blocked(global_job=False):
            return
        logger.info("metadata.ui: explorar_lote")
        archivos = filedialog.askopenfilenames(
            title=t('select_images_clean'),
            filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.tiff *.webp *.heic *.heif')]
        )
        if archivos:
            self._cargar_lote(list(archivos))

    def _cargar_lote(self, rutas: list[str]):
        """Cargar lista de imagenes para procesamiento en lote.

        Args:
            rutas: Lista de rutas de archivos seleccionados
        """
        if self._operation_blocked(global_job=False):
            return
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            msg = t('limit_reached').format(limit=limite, total=total)
            self._lbl_info.configure(text=msg)

        self._state.imagenes_lote = rutas
        build_file_list(
            self._lista_lote, rutas, self._filas_lote, self._thumbs,
            thumb_size=44, show_ext=True
        )
        load_thumbs_async(rutas, self._filas_lote, self._thumbs, self._post_ui, thumb_size=44)
        n = len(rutas)
        self._lbl_info.configure(
            text=f'{n} {t("images_ready_clean")}'
        )

    def _limpiar_lote(self):
        """Iniciar proceso de limpieza de metadatos en lote."""
        if self._operation_blocked(global_job=True):
            return
        logger.info("metadata.ui: limpiar_lote")
        if not self._state.imagenes_lote:
            self._lbl_info.configure(text=t('load_images_first_clean'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder_clean'))
        if not carpeta:
            logger.info("metadata.ui: limpiar_lote_cancelado (sin_carpeta)")
            return
        self._show_full_overlay(t('processing'))
        self._btn_limpiar_exif.configure(state='disabled', text=t('cleaning'))
        paths = tuple(self._state.imagenes_lote)
        self._submit_job(lambda: self._proceso_limpiar(carpeta, paths), button=self._btn_limpiar_exif, text=t('clean_exif'))

    def _proceso_limpiar(self, carpeta: str, paths):
        """Ejecutar limpieza de metadatos en hilo separado.

        Args:
            carpeta: Ruta de la carpeta de salida
        """
        logger.info("metadata.ui: proceso_limpiar_inicio (imagenes=%s)", len(paths))
        res = batch_limpiar_exif(paths, carpeta)
        self._post_ui(0, lambda: self._btn_limpiar_exif.configure(
            state='normal', text=t('clean_exif')
        ))
        msg = f'{res["ok"]} {t("cleaned")}'
        if res['errores']:
            msg += f'  -  {res["errores"]} {t("error_occurred")}'
        if res.get('conflictos'):
            msg += f'  -  {res["conflictos"]} {t("conflicts_renamed")}'
        self._post_ui(0, lambda: self._lbl_info.configure(text=msg))
        logger.info("metadata.ui: limpiar_lote_fin (ok=%s, errores=%s)", res.get("ok"), res.get("errores"))
        self._post_ui(0, self._hide_full_overlay)
        return res

    def _cambiar_tab(self, tab: str):
        """Cambiar el tab visible en el contenedor.

        Args:
            tab: Nombre del tab a mostrar
        """
        for nombre, frame in self._frames.items():
            if nombre == tab:
                frame.tkraise()

    def _limpiar(self):
        """Limpiar todo el estado y reiniciar la interfaz."""
        if self._operation_blocked(global_job=False):
            return
        logger.info("metadata.ui: limpiar")
        self._limpiar_todo()

    def _limpiar_todo(self):
        """Restaurar estado inicial de todos los componentes."""
        if self._operation_blocked(global_job=False):
            return
        logger.info("metadata.ui: limpiar_todo")
        self._state.ruta = None
        self._state.ruta_edicion = None
        self._state.imagenes_lote = []
        self._state.metadatos = {}
        self._thumbs.clear()
        self._filas_lote.clear()
        self._metadata_rows.clear()
        self._metadata_sections.clear()

        for w in self._scroll_meta.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._scroll_meta,
            text=t('no_metadata'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=0, column=0, columnspan=2, pady=20)

        for entry in self._campos_edit.values():
            if isinstance(entry, ctk.CTkComboBox):
                entry.set(t('leave_unchanged'))
            else:
                entry.delete(0, 'end')
        self._sync_dates_var.set(False)
        self._clear_gps_var.set(False)
        self._combo_orientacion.set(t('keep_orientation'))
        self._info_tecnica.configure(text='')

        if hasattr(self, '_lbl_edit_target'):
            self._lbl_edit_target.configure(text=t('select_image_edit'))
        self._edit_preview_source = None
        self._render_preview_edicion()

        for w in self._lista_lote.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._lista_lote,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=12)

        self._lbl_info.configure(text='')
