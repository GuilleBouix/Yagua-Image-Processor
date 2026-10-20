"""Metadata workspace: shared collection, per-image drafts and batch actions."""
from __future__ import annotations

from app.ui.building import stepwise, steps_for
from pathlib import Path
import unicodedata
import webbrowser

import customtkinter as ctk

from app.translations import t
from app.ui import colors, fonts
from app.ui.frames.base import BaseFrame
from app.ui.frames.metadata.collection import MetadataCollection, decode_preview
from app.ui.frames.metadata.state import MetadataState
from app.ui.frames.metadata.widgets import MetadataFiles, MetadataPreview
from app.ui.rendering import configure_changed
from app.ui.frames.metadata.services import (
    CAMPOS_EDITABLES, GRUPOS_CAMPOS_EDITABLES, CAMPOS_VISIBLES,
    GRUPOS_CAMPOS_VISIBLES, OPCIONES_ENUM_EXIF as _ENUM_OPTIONS,
    ORIENTACIONES_EXIF as _ORIENTATION_OPTIONS,
)

_cargar_preview_edicion = decode_preview


class MetadataFrame(BaseFrame):
    def __init__(self, parent, *, defer_build=False):
        self._state = MetadataState()
        self._collection = MetadataCollection(self)
        self._file_views: list[MetadataFiles] = []
        self._previews: list[MetadataPreview] = []
        self._metadata_rows = []
        self._metadata_sections = []
        self._campos_edit: dict[str, ctk.CTkEntry | ctk.CTkComboBox] = {}
        self._enum_values: dict[str, dict[str, str]] = {}
        self._orientacion_values: dict[str, int] = {}
        super().__init__(parent, t('metadata_title'), defer_build=defer_build)

    def destroy(self):
        self._collection.closed.set()
        super().destroy()

    def on_view_hidden(self):
        self._collection.visible = False
        for pane in self._previews:
            pane.set_visible(False)
        self._collection.refresh()

    def on_view_shown(self):
        super().on_view_shown()
        self._collection.visible = True
        self._collection.refresh()
        self._collection.render_previews()

    def _action(self, parent, key, command):
        return ctk.CTkButton(parent, text=t(key), height=36, width=1,
            font=fonts.FUENTE_BASE, fg_color=colors.ACENTO, text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER, command=command)

    def _crear_lista(self, parent, *, row):
        files = MetadataFiles(parent, self._state, self._collection.activate,
                              self._collection.mark, self._collection.mark_all)
        files.grid(row=row, column=0, padx=16, pady=(0, 12), sticky='ew')
        self._file_views.append(files)
        files.tab_frame = parent.master.master
        files.request_thumbnail = self._collection.request_thumbnail
        return files

    def _crear_preview(self, parent, *, row, height=180):
        preview = MetadataPreview(parent, height=height)
        preview.grid(row=row, column=0, padx=16, pady=16, sticky='nsew')
        self._previews.append(preview)
        preview.tab_frame = parent.master.master
        return preview

    @stepwise
    def _build_content(self):
        self.grid_columnconfigure(0, weight=1)
        yield
        self._tab = ctk.CTkSegmentedButton(self, values=[t('view'), t('edit'), t('clean_batch')],
            font=fonts.FUENTE_BASE, selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.PANEL_BG, unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR, command=self._cambiar_tab)
        yield
        self._tab.set(t('view'))
        yield
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 8), sticky='ew')
        yield
        self._contenedor = ctk.CTkFrame(self, fg_color='transparent')
        yield
        self._contenedor.grid(row=2, column=0, sticky='nsew')
        yield
        self._contenedor.grid_columnconfigure(0, weight=1)
        yield
        self._frames = {t('view'): (yield from steps_for(self._build_tab_ver)), t('edit'): (yield from steps_for(self._build_tab_editar)),
                        t('clean_batch'): (yield from steps_for(self._build_tab_limpiar))}
        yield
        for frame in self._frames.values():
            frame.grid(row=0, column=0, sticky='nsew')
            yield
        self._cambiar_tab(t('view'))
        yield

    @stepwise
    def _build_tab_ver(self):
        frame = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        if self._defer_build:
            frame.grid(row=0, column=0, sticky='nsew')
        yield
        left, right = self._crear_workspace(frame, row=0, breakpoint=720, padx=16, pady=0)
        yield
        self._dz_ver = self._crear_boton_seleccionar(left, t('meta_add_images'), self._explorar_lote)
        yield
        self._dz_ver.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield
        self._crear_lista(left, row=1)
        yield
        self._preview_ver = self._crear_preview(left, row=2)
        yield
        ctk.CTkLabel(right, text=t('metadata_title'), anchor='w', font=fonts.FUENTE_BASE).grid(
            row=0, column=0, padx=16, pady=(16, 0), sticky='ew')
        yield
        self._scroll_meta = ctk.CTkScrollableFrame(right, fg_color='transparent', border_width=0, height=380)
        yield
        self._scroll_meta.grid(row=1, column=0, padx=16, pady=8, sticky='nsew')
        yield
        right.grid_rowconfigure(1, weight=1)
        yield
        self._scroll_meta.grid_columnconfigure(0, weight=2, uniform='metadata-columns')
        yield
        self._scroll_meta.grid_columnconfigure(1, weight=3, uniform='metadata-columns')
        yield
        self._scroll_meta.bind('<Configure>', self._ajustar_filas_metadatos, add='+')
        yield
        self._renderizar_metadatos({})
        yield
        self._export_scope = ctk.CTkComboBox(right, values=[t('meta_current'), t('meta_marked')], state='readonly',
            font=fonts.FUENTE_BASE, fg_color=colors.DROPZONE_BG, text_color=colors.TEXT_COLOR)
        yield
        self._export_scope.set(t('meta_current'))
        yield
        self._export_scope.grid(row=2, column=0, padx=16, pady=8, sticky='ew')
        yield
        actions = ctk.CTkFrame(right, fg_color='transparent')
        yield
        actions.grid(row=3, column=0, padx=16, pady=(0, 16), sticky='ew')
        yield
        actions.grid_columnconfigure((0, 1), weight=1)
        yield
        self._action(actions, 'export_txt', lambda: self._exportar('txt')).grid(row=0, column=0, padx=(0, 6), sticky='ew')
        yield
        self._action(actions, 'export_json', lambda: self._exportar('json')).grid(row=0, column=1, padx=(6, 0), sticky='ew')
        yield
        return frame

    @stepwise
    def _build_tab_limpiar(self):
        frame = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        if self._defer_build:
            frame.grid(row=0, column=0, sticky='nsew')
        yield
        left, right = self._crear_workspace(frame, row=0, breakpoint=720, padx=16, pady=0)
        yield
        self._crear_boton_seleccionar(left, t('meta_add_images'), self._explorar_lote).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield
        self._lista_lote = self._crear_lista(left, row=1).list
        yield
        self._btn_limpiar_exif = self._action(left, 'meta_clean_selected', self._limpiar_lote)
        yield
        self._btn_limpiar_exif.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='ew')
        yield
        ctk.CTkLabel(left, text=t('meta_clean_help'), text_color=colors.TEXT_GRAY,
                     font=fonts.FUENTE_CHICA, justify='left', wraplength=300).grid(
                         row=3, column=0, padx=16, pady=(0, 16), sticky='ew')
        yield
        self._preview_limpiar = self._crear_preview(right, row=0)
        yield
        self._summary = ctk.CTkTextbox(right, height=180, fg_color=colors.DROPZONE_BG,
                                      text_color=colors.TEXT_COLOR, font=fonts.FUENTE_CHICA, wrap='word')
        yield
        self._summary.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._summary.configure(state='disabled')
        yield
        return frame

    @stepwise
    def _build_tab_editar(self):
        """Keep the collection compact and give the editor most of the workspace."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        if self._defer_build:
            f.grid(row=0, column=0, sticky='nsew')
        yield
        izquierda, derecha = self._crear_workspace(
            f, row=0, column_weights=(2, 3), breakpoint=800, padx=16, pady=0)
        yield
        btn = self._crear_boton_seleccionar(izquierda, t('meta_add_images'), self._explorar_lote)
        yield
        btn.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield
        self._crear_lista(izquierda, row=1)
        yield
        self._preview_editar = self._crear_preview(izquierda, row=2, height=180)
        yield
        izquierda.grid_rowconfigure(2, weight=1)
        yield
        self._lbl_edit_target = self._preview_editar.name
        yield
        self._lbl_edit_preview = self._preview_editar.image
        yield

        self._edit_target = ctk.CTkLabel(derecha, text=t('meta_current'), anchor='w',
            justify='left', font=fonts.FUENTE_BASE, width=1)
        yield
        self._edit_target.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield
        filters = ctk.CTkFrame(derecha, fg_color='transparent')
        yield
        filters.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')
        yield
        filters.grid_columnconfigure(0, weight=1)
        yield
        self._edit_query = ctk.StringVar()
        yield
        self._edit_search = ctk.CTkEntry(filters, textvariable=self._edit_query,
            placeholder_text=t('meta_search_fields'), height=36, width=1,
            font=fonts.FUENTE_BASE, fg_color=colors.DROPZONE_BG,
            border_color=colors.SIDEBAR_SEPARATOR, text_color=colors.TEXT_COLOR)
        yield
        self._edit_search.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        yield
        groups = [*GRUPOS_CAMPOS_EDITABLES, 'dates', 'orientation']
        yield
        self._edit_sections = {t('meta_all_sections'): None,
                              **{t(f'metadata_section_{group}'): group for group in groups}}
        yield
        self._edit_section = ctk.CTkComboBox(filters, values=list(self._edit_sections),
            state='readonly', width=190, height=36, font=fonts.FUENTE_BASE,
            fg_color=colors.DROPZONE_BG, text_color=colors.TEXT_COLOR,
            command=lambda _value: self._filtrar_campos())
        yield
        self._edit_section.set(t('meta_all_sections'))
        yield
        self._edit_section.grid(row=0, column=1, sticky='ew')
        yield
        # A bounded viewport keeps the form useful without growing the outer page.
        viewport = ctk.CTkFrame(derecha, fg_color='transparent', height=350)
        yield
        viewport.grid(row=2, column=0, padx=16, pady=0, sticky='nsew')
        yield
        viewport.grid_propagate(False)
        yield
        viewport.grid_columnconfigure(0, weight=1)
        yield
        viewport.grid_rowconfigure(0, weight=1)
        yield
        derecha.grid_rowconfigure(2, weight=1)
        yield
        panel = ctk.CTkScrollableFrame(viewport, corner_radius=0, fg_color='transparent',
                                       border_width=0, height=350)
        yield
        self._panel_editar = panel
        yield
        panel.grid(row=0, column=0, sticky='nsew')
        yield
        panel.grid_columnconfigure(0, weight=1)
        yield
        self._edit_groups = {}
        yield
        self._edit_rows = []
        yield
        for index, grupo in enumerate(groups):
            section = ctk.CTkFrame(panel, fg_color='transparent')
            yield
            section.grid(row=index, column=0, sticky='ew', pady=(0, 12))
            yield
            section.grid_columnconfigure(0, weight=1)
            yield
            ctk.CTkLabel(section, text=t(f'metadata_section_{grupo}'), font=fonts.FUENTE_BASE,
                         text_color=colors.TEXT_COLOR, anchor='w').grid(
                             row=0, column=0, sticky='ew', pady=(6, 8))
            yield
            self._edit_groups[grupo] = section
            yield
            campos = GRUPOS_CAMPOS_EDITABLES.get(grupo, ('DateTimeOriginal',) if grupo == 'dates' else ())
            yield
            fila = 1
            yield
            for campo in campos:
                row = self._fila_editor(section, grupo, campo, t(CAMPOS_EDITABLES[campo]), fila)
                yield
                self._agregar_campo_edicion(row, campo, 0)
                yield
                fila += 1
                yield
            if grupo == 'gps':
                self._clear_gps_var = ctk.BooleanVar(value=False)
                yield
                row = self._fila_editor(section, grupo, 'clear_gps', t('clear_gps'), fila)
                yield
                self._clear_gps_check = ctk.CTkCheckBox(
                    row, text=t('clear_gps'), variable=self._clear_gps_var,
                    font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR,
                )
                yield
                self._clear_gps_check.grid(row=0, column=0, columnspan=2, pady=8, sticky='w')
                yield
            elif grupo == 'dates':
                self._sync_dates_var = ctk.BooleanVar(value=False)
                yield
                row = self._fila_editor(section, grupo, 'sync_dates', t('sync_dates'), fila)
                yield
                self._sync_dates_check = ctk.CTkCheckBox(row, text=t('sync_dates'),
                    variable=self._sync_dates_var, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR)
                yield
                self._sync_dates_check.grid(row=0, column=0, columnspan=2, pady=8, sticky='w')
                yield
            elif grupo == 'orientation':
                row = self._fila_editor(section, grupo, 'orientation', t('orientation_transform'), fila)
                yield
                ctk.CTkLabel(row, text=t('orientation_transform'), font=fonts.FUENTE_BASE,
                             text_color=colors.TEXT_GRAY, anchor='w').grid(row=0, column=0, sticky='w')
                yield
                self._combo_orientacion = ctk.CTkComboBox(row,
                    values=[t('keep_orientation')] + [t(key) for key in _ORIENTATION_OPTIONS.values()],
                    state='readonly', height=36, font=fonts.FUENTE_BASE,
                    fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
                    text_color=colors.TEXT_COLOR)
                yield
                self._combo_orientacion.set(t('keep_orientation'))
                yield
                self._orientacion_values = {t(key): value for value, key in _ORIENTATION_OPTIONS.items()}
                yield
                self._combo_orientacion.grid(row=0, column=1, sticky='ew', padx=(12, 4))
                yield
        self._edit_no_results = ctk.CTkLabel(panel, text=t('meta_no_matching_fields'),
            font=fonts.FUENTE_BASE, text_color=colors.TEXT_GRAY)
        yield
        self._edit_no_results.grid(row=len(groups), column=0, pady=24)
        yield
        self._edit_no_results.grid_remove()
        yield
        self._info_tecnica = ctk.CTkLabel(
            derecha, text='', font=fonts.FUENTE_CHICA, width=1,
            text_color=colors.TEXT_GRAY, anchor='w', justify='left'
        )
        yield
        self._info_tecnica.grid(row=3, column=0, padx=16, pady=(4, 0), sticky='ew')
        yield
        derecha.bind('<Configure>', lambda event: self._ajustar_editor(event.width), add='+')
        yield
        self._edit_query.trace_add('write', lambda *_args: self._filtrar_campos())
        yield
        actions = ctk.CTkFrame(derecha, fg_color='transparent')
        yield
        actions.grid(row=4, column=0, padx=16, pady=(8, 16), sticky='ew')
        yield
        actions.grid_columnconfigure((0, 1), weight=1)
        yield
        self._btn_apply_fields = self._action(actions, 'meta_copy_fields', self._collection.choose_fields)
        yield
        self._btn_apply_fields.configure(fg_color='transparent', border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR, text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER)
        yield
        self._btn_apply_fields.grid(row=0, column=0, padx=(0, 6), sticky='ew')
        yield
        self._btn_guardar_edit = self._action(actions, 'meta_save', lambda: self._collection.save(selected=None))
        yield
        self._btn_guardar_edit.grid(row=0, column=1, padx=(6, 0), sticky='ew')
        yield
        return f

    def _fila_editor(self, section, group, field, label, row):
        container = ctk.CTkFrame(section, fg_color='transparent')
        container.grid(row=row, column=0, sticky='ew', pady=4)
        container.grid_columnconfigure(0, weight=2, uniform='edit-fields')
        container.grid_columnconfigure(1, weight=3, uniform='edit-fields')
        self._edit_rows.append((group, field, label, container))
        return container

    @staticmethod
    def _texto_busqueda(text):
        return ''.join(char for char in unicodedata.normalize('NFKD', text.casefold())
                       if not unicodedata.combining(char))

    def _filtrar_campos(self):
        query = self._texto_busqueda(self._edit_query.get().strip())
        selected = self._edit_sections.get(self._edit_section.get())
        visible_groups = set()
        for group, field, label, row in self._edit_rows:
            matches = (selected is None or selected == group) and query in self._texto_busqueda(
                f'{label} {field} {t(f"metadata_section_{group}")}')
            if matches:
                row.grid()
                visible_groups.add(group)
            else:
                row.grid_remove()
        for group, section in self._edit_groups.items():
            if group in visible_groups:
                section.grid()
            else:
                section.grid_remove()
        if visible_groups:
            self._edit_no_results.grid_remove()
        else:
            self._edit_no_results.grid()
        self._panel_editar._parent_canvas.yview_moveto(0)

    def _ajustar_editor(self, width):
        logical = max(200, int(width / self._get_widget_scaling()) - 40)
        self._edit_target.configure(wraplength=logical)
        self._info_tecnica.configure(wraplength=logical)
        for _, _, _, row in self._edit_rows:
            for child in row.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(wraplength=max(80, int(logical * .4) - 16))

    def _agregar_campo_edicion(self, panel, campo: str, fila: int) -> int:
        etiqueta = t(CAMPOS_EDITABLES[campo])
        ctk.CTkLabel(
            panel, text=etiqueta, font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w',
            justify='left', width=1,
        ).grid(row=fila, column=0, padx=(0, 12), pady=4, sticky='ew')

        if campo in _ENUM_OPTIONS:
            opciones = {t(clave): str(valor) for valor, clave in _ENUM_OPTIONS[campo].items()}
            self._enum_values[campo] = opciones
            widget = ctk.CTkComboBox(
                panel, values=[t('leave_unchanged')] + list(opciones),
                state='readonly', font=fonts.FUENTE_BASE, height=36,
                fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
            )
            widget.set(t('leave_unchanged'))
        else:
            placeholder = t('datetime_format_placeholder') if campo == 'DateTimeOriginal' else t('enter_field').format(etiqueta.lower())
            widget = ctk.CTkEntry(
                panel, font=fonts.FUENTE_BASE, height=36,
                fg_color=colors.FRAMES_BG, border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR, placeholder_text=placeholder,
                placeholder_text_color=colors.TEXT_GRAY,
            )
        widget.grid(row=fila, column=1, padx=(0, 4), pady=4, sticky='ew')
        self._campos_edit[campo] = widget
        return fila + 1


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
            configure_changed(etiqueta, wraplength=max(60, int(ancho * .4) - 12))
            configure_changed(valor, wraplength=max(80, int(ancho * .6) - 12))
        for seccion in self._metadata_sections:
            configure_changed(seccion, wraplength=ancho)


    def _renderizar_metadatos(self, metadatos: dict[str, str]):
        """Update known rows in place; never rebuild the metadata table."""
        if not hasattr(self, '_meta_row_cache'):
            self._meta_row_cache = {}
            self._meta_section_cache = {}
            self._meta_empty = ctk.CTkLabel(self._scroll_meta, text=t('no_metadata_image'),
                font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY)
        previous = {name for name, _, _ in self._metadata_rows}
        previous_sections = set(self._metadata_sections)
        self._metadata_rows = []
        self._metadata_sections = []
        fila = 0
        gps = metadatos.get('__gps_decimal__')
        for grupo, nombres in GRUPOS_CAMPOS_VISIBLES.items():
            campos = [name for name in nombres if metadatos.get(CAMPOS_VISIBLES[name][0], '').strip()]
            if not campos:
                continue
            seccion = self._meta_section_cache.get(grupo)
            if seccion is None:
                seccion = ctk.CTkLabel(self._scroll_meta, text=t(f'metadata_section_{grupo}'),
                    font=fonts.FUENTE_BASE, text_color=colors.TEXT_COLOR, anchor='w', justify='left')
                self._meta_section_cache[grupo] = seccion
            if seccion not in previous_sections or int(seccion.grid_info().get('row', -1)) != fila:
                seccion.grid(row=fila, column=0, columnspan=2, padx=8, pady=(12 if fila else 4, 6), sticky='ew')
            self._metadata_sections.append(seccion)
            fila += 1
            for nombre in campos:
                clave, traduccion = CAMPOS_VISIBLES[nombre]
                if nombre not in self._meta_row_cache:
                    etiqueta = ctk.CTkLabel(self._scroll_meta, text=t(traduccion), font=fonts.FUENTE_CHICA,
                        text_color=colors.TEXT_GRAY, anchor='nw', justify='left')
                    valor = ctk.CTkLabel(self._scroll_meta, text='', font=fonts.FUENTE_CHICA,
                        text_color=colors.TEXT_COLOR, anchor='nw', justify='left')
                    self._meta_row_cache[nombre] = (etiqueta, valor)
                etiqueta, valor = self._meta_row_cache[nombre]
                if nombre not in previous or int(etiqueta.grid_info().get('row', -1)) != fila:
                    etiqueta.grid(row=fila, column=0, padx=(8, 4), pady=4, sticky='new')
                    valor.grid(row=fila, column=1, padx=(4, 8), pady=4, sticky='new')
                texto = self._valor_metadato_visible(nombre, metadatos[clave])
                es_mapa = nombre in ('GPSLatitude', 'GPSLongitude') and bool(gps)
                if es_mapa:
                    texto += f'  →  {t("view_on_maps")}'
                configure_changed(valor, text=texto, text_color=colors.ACENTO if es_mapa else colors.TEXT_COLOR,
                                  cursor='hand2' if es_mapa else '')
                url = f'https://maps.google.com/?q={gps}' if es_mapa else None
                if getattr(valor, '_gps_link', None) != url:
                    valor._gps_link = url
                    if url:
                        valor.bind('<Button-1>', lambda _, u=url: webbrowser.open(u))
                    else:
                        valor.unbind('<Button-1>')
                self._metadata_rows.append((nombre, etiqueta, valor))
                fila += 1
        active = {name for name, _, _ in self._metadata_rows}
        for name in previous - active:
            for widget in self._meta_row_cache[name]:
                widget.grid_remove()
        for section in previous_sections - set(self._metadata_sections):
            section.grid_remove()
        if self._metadata_rows:
            self._meta_empty.grid_remove()
        else:
            configure_changed(self._meta_empty, text=t('no_metadata_image'))
            self._meta_empty.grid(row=0, column=0, columnspan=2, pady=20)
        self._ajustar_filas_metadatos()


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


    def _aplicar_campos_edit(self, meta: dict):
        """Aplicar metadatos a los campos editables."""
        for campo, widget in self._campos_edit.items():
            valor = meta.get(campo, '')
            if isinstance(widget, ctk.CTkComboBox):
                display = next(
                    (label for label, code in self._enum_values[campo].items() if code == str(valor)),
                    t('leave_unchanged'),
                )
                if widget.get() != display:
                    widget.set(display)
            else:
                if widget.get() != str(valor):
                    widget.delete(0, 'end')
                    if valor:
                        widget.insert(0, valor)
        self._loaded_edit_values = {key: (self._enum_values[key].get(widget.get(), '') if key in self._enum_values else widget.get().strip()) for key, widget in self._campos_edit.items()}
        self._sync_dates_var.set(False)
        self._clear_gps_var.set(False)
        self._combo_orientacion.set(t('keep_orientation'))
        try:
            orientation = int(meta.get('__orientation__', 1))
        except (ValueError, TypeError):
            orientation = 1
        orientation_key = _ORIENTATION_OPTIONS.get(orientation, 'orient_normal')
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


    def _explorar_lote(self):
        self._collection.explore()

    def _explorar_ver(self):
        self._collection.explore()

    def _explorar_editar(self):
        self._collection.explore()

    def _cargar_lote(self, rutas):
        self._collection.add(rutas)

    def _guardar_edicion(self):
        self._collection.save()

    def _limpiar_lote(self):
        self._collection.save(selected=True, clean=True)

    def _exportar(self, fmt):
        self._collection.export(fmt)

    def _cambiar_tab(self, tab):
        self._collection.change_tab(tab)

    def _limpiar(self):
        self._collection.clear()

    def _limpiar_todo(self):
        self._collection.clear()
