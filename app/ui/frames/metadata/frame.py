"""Espacio de trabajo EXIF con catálogo compartido, borradores por imagen y acciones por lote."""
from __future__ import annotations

from app.ui.building import stepwise, steps_for
import unicodedata
import webbrowser

import customtkinter as ctk

from app.translations import t
from app.ui import colors, fonts, styles
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
    """Orquesta las pestañas de consulta, limpieza y edición EXIF."""
    design_system = True

    def __init__(self, parent, *, defer_build=False):
        """Inicializa el estado del módulo y construye sus paneles."""
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
        """Invalida la vista y libera callbacks y recursos asociados."""
        self._collection.closed.set()
        super().destroy()

    def _on_build_complete(self):
        """Conecta acciones cuando la construcción diferida termina."""
        self._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        for panel in (self._scroll_meta, self._panel_editar):
            panel._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        self._summary._y_scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        self._summary._x_scrollbar.configure(corner_radius=0, height=6, border_spacing=1)
        self._collection.refresh()
        self._collection.render_previews()

    def _schedule_viewport_sync(self, _event=None):
        # Espera el ciclo idle de grid después de cambiar de pestaña o
        # mostrar controles. Un callback idle puede seguir viendo la geometría anterior.
        """Ajusta el área desplazable después de actualizar contenido."""
        if self._viewport_sync_job is None and self.winfo_exists():
            self._viewport_sync_job = self.after(16, self._sync_viewport_height)

    @staticmethod
    def _show_control(widget, visible):
        """Actualiza la visibilidad de los controles según la pestaña activa."""
        if visible and not widget.winfo_manager():
            widget.grid()
        elif not visible and widget.winfo_manager():
            widget.grid_remove()

    def _sync_presentation(self):
        """Sincroniza título, selección y paneles con el estado del módulo."""
        if not self.build_ready:
            return
        current = self._state.current
        has_images = bool(self._state.items)
        ready = bool(current and self._collection.preview_token == (
            self._collection.epoch, self._collection.revision, self._state.active))
        data = current.data if current and ready else None
        editable = bool(data and data['editable'] and not data['edit_error'])
        can_save = editable or any(item.draft.dirty for item in self._state.marked)
        for preview in self._previews:
            self._show_control(preview, current is not None)
            if current is None:
                preview.set_visible(False)
        for widget in (self._meta_heading, self._scroll_meta):
            self._show_control(widget, current is not None)
        for widget in (self._export_scope, self._export_actions):
            self._show_control(widget, data is not None)
        self._show_control(self._edit_target, current is not None)
        for widget in (self._edit_filters, self._edit_viewport, self._info_tecnica):
            self._show_control(widget, editable)
        for widget in (self._edit_actions, self._edit_save_group):
            self._show_control(widget, can_save)
        self._show_control(self._edit_message, current is not None and not editable)
        message = t('reading_metadata') if not ready else (
            t('meta_read_error') if data is None else
            t('meta_read_only_short') if not data['edit_error'] else t('error_generic'))
        configure_changed(self._edit_message, text=message)
        for widget in (self._btn_limpiar_exif, self._clean_save_group):
            self._show_control(widget, has_images)
        self._show_control(self._result_bar, bool(self._collection.summary))
        self._show_control(self._summary, bool(self._collection.summary) and self._collection.details_expanded)
        configure_changed(self._result_text, text=self._collection.summary)
        configure_changed(self._details_button, text=t(
            'meta_hide_details' if self._collection.details_expanded else 'meta_show_details'))
        # Al cambiar visibilidad puede variar el tamaño sin emitir necesariamente
        # Configure: el canvas exterior puede conservar la altura de la pestaña anterior.
        self._schedule_viewport_sync()

    def on_view_hidden(self):
        """Invalida cargas visuales que no deben terminar en una pestaña oculta."""
        self._collection.visible = False
        for pane in self._previews:
            pane.set_visible(False)
        self._collection.refresh()

    def on_view_shown(self):
        """Refresca la presentación al volver a mostrar el módulo."""
        super().on_view_shown()
        self._collection.visible = True
        self._collection.refresh()
        self._collection.render_previews()

    def _action(self, parent, key, command, *, role='primary', height=40):
        """Ejecuta una acción sobre la selección capturada del catálogo."""
        return self._new_button(parent, role=role, text=t(key), height=height, width=1,
            font=fonts.FUENTE_BASE, command=command)

    def _crear_lista(self, parent, *, row):
        """Construye listas virtualizadas para archivos EXIF."""
        files = MetadataFiles(parent, self._state, self._collection.activate,
                              self._collection.mark, self._collection.mark_all)
        files.grid(row=row, column=0, padx=16, pady=(0, 12), sticky='ew')
        self._file_views.append(files)
        files.tab_frame = parent.master.master
        files.request_thumbnail = self._collection.request_thumbnail
        return files

    def _crear_preview(self, parent, *, row, height=180):
        """Crea el panel de vista previa reutilizable."""
        preview = MetadataPreview(parent, height=height)
        preview.grid(row=row, column=0, padx=16, pady=16, sticky='nsew')
        self._previews.append(preview)
        preview.tab_frame = parent.master.master
        return preview

    @stepwise
    def _build_content(self):
        """Construye las pestañas y paneles del editor EXIF."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        yield
        self._tab = styles.SegmentedButton(self, values=[t('view'), t('edit'), t('clean_batch')],
            font=fonts.FUENTE_BASE, command=self._cambiar_tab)
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
        self._contenedor.grid_rowconfigure(0, weight=1)
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
        """Construye la consulta de metadatos de la pestaña Ver."""
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
        self._meta_heading = ctk.CTkLabel(right, text=t('metadata_title'), anchor='w', font=fonts.FUENTE_BASE)
        self._meta_heading.grid(row=0, column=0, padx=16, pady=(16, 0), sticky='ew')
        yield
        self._scroll_meta = ctk.CTkScrollableFrame(right, fg_color='transparent', corner_radius=0,
            border_width=0, height=380, **styles.scrollbar())
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
        self._export_scope = styles.ComboBox(right, values=[t('meta_current'), t('meta_marked')], state='readonly',
            font=fonts.FUENTE_BASE)
        yield
        self._export_scope.set(t('meta_current'))
        yield
        self._export_scope.grid(row=2, column=0, padx=16, pady=8, sticky='ew')
        yield
        actions = ctk.CTkFrame(right, fg_color='transparent')
        self._export_actions = actions
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
        """Construye selección y acciones de limpieza EXIF."""
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
        yield from self._build_save_selector(left, 2)
        self._clean_save_group = self._save_groups[-1]
        self._btn_limpiar_exif.grid(row=3, column=0, padx=16, pady=(0, 16), sticky='ew')
        yield
        self._preview_limpiar = self._crear_preview(right, row=0)
        yield
        self._result_bar = ctk.CTkFrame(right, fg_color='transparent')
        self._result_bar.grid(row=1, column=0, padx=16, pady=(0, 12), sticky='ew')
        self._result_bar.grid_columnconfigure(0, weight=1)
        yield
        self._result_text = ctk.CTkLabel(self._result_bar, text='', width=1,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR, anchor='w', justify='left', wraplength=280)
        self._result_text.grid(row=0, column=0, sticky='ew')
        self._result_bar.bind('<Configure>', lambda event: configure_changed(self._result_text,
            wraplength=max(100, int(event.width / self._get_widget_scaling()) - 140)), add=True)
        yield
        self._details_button = self._action(self._result_bar, 'meta_show_details', self._collection.toggle_details,
            role='secondary', height=30)
        self._details_button.grid(row=0, column=1, padx=(12, 0), sticky='e')
        yield
        self._summary = ctk.CTkTextbox(right, height=180, **styles.surface('list'),
            scrollbar_button_color=styles.scrollbar()['scrollbar_button_color'],
            scrollbar_button_hover_color=styles.scrollbar()['scrollbar_button_hover_color'],
            text_color=colors.TEXT_COLOR, font=fonts.FUENTE_CHICA, wrap='word')
        yield
        self._summary.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._summary.configure(state='disabled')
        yield
        return frame

    @stepwise
    def _build_tab_editar(self):
        """Mantiene compacto el catálogo y reserva el espacio principal para el editor."""
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
        self._preview_editar = self._crear_preview(izquierda, row=2, height=100)
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
        self._edit_filters = filters
        yield
        filters.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')
        yield
        filters.grid_columnconfigure(0, weight=1)
        yield
        self._edit_query = ctk.StringVar()
        yield
        self._edit_search = styles.Entry(filters, textvariable=self._edit_query,
            placeholder_text=t('meta_search_fields'), height=36, width=1,
            font=fonts.FUENTE_BASE)
        yield
        self._edit_search.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        yield
        groups = [*GRUPOS_CAMPOS_EDITABLES, 'dates', 'orientation']
        yield
        self._edit_sections = {t('meta_all_sections'): None,
                              **{t(f'metadata_section_{group}'): group for group in groups}}
        yield
        self._edit_section = styles.ComboBox(filters, values=list(self._edit_sections),
            state='readonly', width=190, height=36, font=fonts.FUENTE_BASE,
            command=lambda _value: self._filtrar_campos())
        yield
        self._edit_section.set(t('meta_all_sections'))
        yield
        self._edit_section.grid(row=0, column=1, sticky='ew')
        yield
        # Un mínimo bajo permite usar el alto disponible sin empujar
        # las acciones de guardado fuera de la ventana. El espacio extra amplía esta fila.
        viewport = ctk.CTkFrame(derecha, fg_color='transparent', height=220)
        self._edit_viewport = viewport
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
                                       border_width=0, height=220, **styles.scrollbar())
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
                self._clear_gps_check = styles.CheckBox(
                    row, text=t('clear_gps'), variable=self._clear_gps_var,
                    font=fonts.FUENTE_CHICA,
                )
                yield
                self._clear_gps_check.grid(row=0, column=0, columnspan=2, pady=8, sticky='w')
                yield
            elif grupo == 'dates':
                self._sync_dates_var = ctk.BooleanVar(value=False)
                yield
                row = self._fila_editor(section, grupo, 'sync_dates', t('sync_dates'), fila)
                yield
                self._sync_dates_check = styles.CheckBox(row, text=t('sync_dates'),
                    variable=self._sync_dates_var, font=fonts.FUENTE_CHICA)
                yield
                self._sync_dates_check.grid(row=0, column=0, columnspan=2, pady=8, sticky='w')
                yield
            elif grupo == 'orientation':
                row = self._fila_editor(section, grupo, 'orientation', t('orientation_transform'), fila)
                yield
                ctk.CTkLabel(row, text=t('orientation_transform'), font=fonts.FUENTE_BASE,
                             text_color=colors.TEXT_GRAY, anchor='w').grid(row=0, column=0, sticky='w')
                yield
                self._combo_orientacion = styles.ComboBox(row,
                    values=[t('keep_orientation')] + [t(key) for key in _ORIENTATION_OPTIONS.values()],
                    state='readonly', height=36, font=fonts.FUENTE_BASE)
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
        yield from self._build_save_selector(derecha, 4)
        self._edit_save_group = self._save_groups[-1]

        actions = ctk.CTkFrame(derecha, fg_color='transparent')
        self._edit_actions = actions
        yield
        actions.grid(row=5, column=0, padx=16, pady=(8, 16), sticky='ew')
        yield
        actions.grid_columnconfigure((0, 1), weight=1)
        yield
        self._btn_apply_fields = self._action(actions, 'meta_copy_fields', self._collection.choose_fields,
            role='secondary')
        yield
        self._btn_apply_fields.grid(row=0, column=0, padx=(0, 6), sticky='ew')
        yield
        self._btn_guardar_edit = self._action(actions, 'meta_save', lambda: self._collection.save(selected=None))
        yield
        self._btn_guardar_edit.grid(row=0, column=1, padx=(6, 0), sticky='ew')
        yield
        self._edit_message = ctk.CTkLabel(derecha, text='', font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, width=1, anchor='center', justify='center', wraplength=260)
        self._edit_message.grid(row=2, column=0, padx=16, pady=24, sticky='nsew')
        self._edit_message.grid_remove()
        yield
        return f

    def _fila_editor(self, section, group, field, label, row):
        """Crea una fila para editar una etiqueta EXIF."""
        container = ctk.CTkFrame(section, fg_color='transparent')
        container.grid(row=row, column=0, sticky='ew', pady=4)
        container.grid_columnconfigure(0, weight=2, uniform='edit-fields')
        container.grid_columnconfigure(1, weight=3, uniform='edit-fields')
        self._edit_rows.append((group, field, label, container))
        return container

    @staticmethod
    def _texto_busqueda(text):
        """Crea el campo usado para filtrar etiquetas editables."""
        return ''.join(char for char in unicodedata.normalize('NFKD', text.casefold())
                       if not unicodedata.combining(char))

    def _filtrar_campos(self):
        """Muestra solo etiquetas que coinciden con la búsqueda."""
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
        """Ajusta el editor al ancho disponible."""
        logical = max(200, int(width / self._get_widget_scaling()) - 40)
        self._edit_target.configure(wraplength=logical)
        self._info_tecnica.configure(wraplength=logical)
        for _, _, _, row in self._edit_rows:
            for child in row.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(wraplength=max(80, int(logical * .4) - 16))

    def _agregar_campo_edicion(self, panel, campo: str, fila: int) -> int:
        """Agrega el control correcto según el tipo de etiqueta EXIF."""
        etiqueta = t(CAMPOS_EDITABLES[campo])
        ctk.CTkLabel(
            panel, text=etiqueta, font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w',
            justify='left', width=1,
        ).grid(row=fila, column=0, padx=(0, 12), pady=4, sticky='ew')

        if campo in _ENUM_OPTIONS:
            opciones = {t(clave): str(valor) for valor, clave in _ENUM_OPTIONS[campo].items()}
            self._enum_values[campo] = opciones
            widget = styles.ComboBox(
                panel, values=[t('leave_unchanged')] + list(opciones),
                state='readonly', font=fonts.FUENTE_BASE, height=36,
            )
            widget.set(t('leave_unchanged'))
        else:
            placeholder = t('datetime_format_placeholder') if campo == 'DateTimeOriginal' else t('enter_field').format(etiqueta.lower())
            widget = styles.Entry(
                panel, font=fonts.FUENTE_BASE, height=36,
                placeholder_text=placeholder,
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
            self._scroll_meta.grid()
        else:
            current = self._state.current
            ready = self._collection.preview_token == (self._collection.epoch, self._collection.revision, self._state.active)
            text = '' if current is None else t('reading_metadata') if not ready else (
                t('no_metadata_image') if current.data is not None else t('meta_read_error'))
            configure_changed(self._meta_empty, text=text)
            if text:
                self._meta_empty.grid(row=0, column=0, columnspan=2, pady=20)
            else:
                self._meta_empty.grid_remove()
        self._ajustar_filas_metadatos()


    def _aplicar_metadatos(self, meta: dict[str, str]):
        """Aplicar metadatos leidos a la interfaz.

        Args:
            meta: Diccionario con los metadatos leidos
        """
        self._state.metadatos = meta
        self._renderizar_metadatos(meta)
        self._hide_full_overlay()


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
        self._hide_full_overlay()


    def _explorar_lote(self):
        """Abre el diálogo para agregar varias imágenes al catálogo."""
        self._collection.explore()

    def _explorar_ver(self):
        """Abre una imagen en el flujo de consulta."""
        self._collection.explore()

    def _explorar_editar(self):
        """Abre una imagen para cargar sus datos en el formulario de edición."""
        self._collection.explore()

    def _cargar_lote(self, rutas):
        """Solicita lectura asíncrona para las imágenes elegidas."""
        self._collection.add(rutas)

    def _guardar_edicion(self):
        """Valida los campos actuales y solicita el guardado de la imagen editada."""
        self._collection.save()

    def _limpiar_lote(self):
        """Quita archivos del lote sin tocar los originales."""
        self._collection.save(selected=True, clean=True)

    def _exportar(self, fmt):
        """Exporta los metadatos de la imagen o selección activa."""
        self._collection.export(fmt)

    def _cambiar_tab(self, tab):
        """Cambia la vista activa y sincroniza el estado del catálogo."""
        self._collection.change_tab(tab)

    def _limpiar(self):
        """Limpia los campos del editor y restablece selectores."""
        self._collection.clear()

    def _limpiar_todo(self):
        """Limpia el formulario y restablece también los selectores."""
        self._collection.clear()
