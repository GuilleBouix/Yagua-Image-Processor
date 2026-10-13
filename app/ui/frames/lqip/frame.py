"""Espacio técnico para generar, comparar y exportar LQIP / Base64."""

from __future__ import annotations

import logging
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Thread
from tkinter import TclError, filedialog, font as tkfont

import customtkinter as ctk
from PIL import Image

from app.modules.compress import formatear_bytes
from app.translations import t as _translate
from app.ui import colors, fonts
from app.ui.frames.base import BaseFrame
from app.ui.frames.lqip.services import (
    ItemResult, SourcePreview, cargar_original, exportar_json, exportar_txt,
    procesar_archivos,
)
from app.ui.frames.lqip.state import LqipState
from app.ui.operations import operations

logger = logging.getLogger(__name__)
CODE_PREVIEW_LIMIT = 12_000


def t(key: str) -> str:
    """Los textos del módulo siempre son cadenas, incluso sin traducción."""
    return _translate(key) or key


def _peso(byte_count):
    return f'{byte_count} B' if byte_count < 1024 else formatear_bytes(byte_count)


class LqipFrame(BaseFrame):
    """Entrada y ajustes a la izquierda; comparación y código a la derecha."""

    def __init__(self, parent):
        self._state = LqipState()
        self._selected_index: int | None = None
        self._results: dict[int, ItemResult] = {}
        self._sources: dict[int, SourcePreview] = {}
        self._resetting = False
        self._revision = 0
        self._source_revision = 0
        self._busy = False
        self._ui_ready = False
        self._source_queue: SimpleQueue[tuple[int, SourcePreview]] = SimpleQueue()
        self._source_job = None
        self._render_job = None
        self._display_images = {}
        self._left_help_labels = []
        self._traces = []
        super().__init__(parent, t('lqip_title'))
        self._ui_ready = True
        for variable in (
            self._state.modo, self._state.ancho_lqip, self._state.blur,
            self._state.calidad_lqip, self._state.calidad_b64,
        ):
            token = variable.trace_add('write', self._ajustes_cambiados)
            self._traces.append((variable, token))
        self._source_job = self.after(40, self._recibir_originales)
        self._actualizar_validacion()
        self._actualizar_acciones()
        self._programar_render()

    def _text_label(self, parent, text='', *, muted=False, **kwargs):
        return ctk.CTkLabel(
            parent, text=text, anchor='w', justify='left',
            font=fonts.FUENTE_CHICA if muted else fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY if muted else colors.TEXT_COLOR,
            height=18 if muted else 22, **kwargs,
        )

    def _build_content(self):
        left, right = self._crear_workspace(column_weights=(2, 3), breakpoint=900)
        self._left = left
        self._right = right
        self._workspace_host.bind('<Configure>', self._schedule_viewport_sync, add=True)
        right.grid_rowconfigure(7, weight=1)
        self._btn_seleccionar = self._crear_boton_seleccionar(
            left, texto=t('lqip_select_image'),
            comando=lambda: self._explorar(titulo=t('lqip_select_image'), multi=False),
        )
        self._btn_seleccionar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        self._lbl_input_name = self._text_label(left, t('lqip_select_hint'), wraplength=330)
        self._lbl_input_name.grid(row=1, column=0, padx=16, pady=(0, 2), sticky='ew')
        self._lbl_input_meta = self._text_label(left, '—', muted=True, wraplength=330)
        self._lbl_input_meta.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='ew')

        header = ctk.CTkFrame(left, fg_color='transparent')
        header.grid(row=3, column=0, padx=16, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        self._text_label(header, t('lqip_generation')).grid(row=0, column=0, sticky='w')
        self._modo_a_interno = {t('lqip_mode_lqip'): 'lqip', t('lqip_mode_b64'): 'base64'}
        self._modo_visible = ctk.StringVar(value=t('lqip_mode_lqip'))
        self._seg_modo = ctk.CTkSegmentedButton(
            header, values=list(self._modo_a_interno), variable=self._modo_visible,
            font=fonts.FUENTE_CHICA, selected_color=colors.SIDEBAR_HOVER,
            selected_hover_color=colors.SIDEBAR_HOVER,
            unselected_color=colors.SIDEBAR_BG, unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR, command=self._cambiar_modo,
        )
        self._seg_modo.grid(row=0, column=1, sticky='e')
        self._lbl_descripcion = self._text_label(left, t('lqip_mode_lqip_desc'), muted=True, wraplength=330)
        self._lbl_descripcion.grid(row=4, column=0, padx=16, pady=(6, 8), sticky='ew')
        self._frame_opciones_modo = ctk.CTkFrame(left, fg_color='transparent')
        self._frame_opciones_modo.grid(row=5, column=0, padx=16, sticky='ew')
        self._frame_opciones_modo.grid_columnconfigure(0, weight=1)
        self._lqip_options = ctk.CTkFrame(self._frame_opciones_modo, fg_color='transparent')
        self._b64_options = ctk.CTkFrame(self._frame_opciones_modo, fg_color='transparent')
        for frame in (self._lqip_options, self._b64_options):
            frame.grid_columnconfigure(0, weight=1)
        self._entry_width, self._error_width = self._campo_numerico(
            self._lqip_options, 0, 'lqip_width', 'lqip_width_help', self._state.ancho_lqip,
        )
        self._entry_blur, self._error_blur = self._campo_numerico(
            self._lqip_options, 3, 'lqip_blur', 'lqip_blur_help', self._state.blur,
        )
        self._lbl_cal_lqip = self._calidad(self._lqip_options, 6, self._state.calidad_lqip, 80)
        self._lbl_cal_b64 = self._calidad(self._b64_options, 0, self._state.calidad_b64, 100)
        self._lqip_options.grid(row=0, column=0, sticky='ew')
        self._btn_procesar = ctk.CTkButton(
            left, text=t('lqip_btn_process'), height=38, font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO, text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER, command=self._procesar,
        )
        self._btn_procesar.grid(row=6, column=0, padx=16, pady=(12, 16), sticky='ew')

        self._lbl_result_name = self._text_label(right, t('lqip_result'), wraplength=500)
        self._lbl_result_name.grid(row=0, column=0, padx=16, pady=(16, 0), sticky='ew')
        self._lbl_result_status = self._text_label(right, t('lqip_select_hint'), muted=True, wraplength=500)
        self._lbl_result_status.grid(row=1, column=0, padx=16, pady=(2, 8), sticky='ew')
        self._comparison = ctk.CTkFrame(right, fg_color='transparent', height=200)
        self._comparison.grid(row=2, column=0, padx=16, sticky='ew')
        self._comparison.grid_propagate(False)
        self._comparison.grid_columnconfigure((0, 1), weight=1, uniform='previews')
        self._comparison.grid_rowconfigure(0, weight=1)
        self._original_label, self._original_meta = self._preview_card(0, 'lqip_original')
        self._output_label, self._output_meta = self._preview_card(1, 'lqip_result')
        self._comparison.bind('<Configure>', self._programar_render, add=True)
        self._lbl_metrics = self._text_label(right, t('lqip_metrics_hint'), muted=True)
        self._lbl_metrics.grid(row=3, column=0, padx=16, pady=(8, 10), sticky='ew')
        self._text_label(right, t('lqip_code')).grid(row=4, column=0, padx=16, pady=(0, 6), sticky='w')
        self._campo_a_clave = {
            t('lqip_field_data_uri'): 'data_uri', t('lqip_field_html_tag'): 'html_tag',
            t('lqip_field_css_bg'): 'css_bg', t('lqip_field_base64'): 'base64',
        }
        self._campo_export = ctk.StringVar(value=t('lqip_field_data_uri'))
        self._seg_formato = ctk.CTkSegmentedButton(
            right, values=list(self._campo_a_clave), variable=self._campo_export,
            font=fonts.FUENTE_CHICA, selected_color=colors.SIDEBAR_HOVER,
            selected_hover_color=colors.SIDEBAR_HOVER,
            unselected_color=colors.SIDEBAR_BG, unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR, command=lambda _: self._actualizar_codigo(),
        )
        self._seg_formato.grid(row=5, column=0, padx=16, sticky='ew')
        self._lbl_format_help = self._text_label(right, '', muted=True, wraplength=500)
        self._lbl_format_help.grid(row=6, column=0, padx=16, pady=(6, 6), sticky='ew')
        fixed = tkfont.nametofont('TkFixedFont').actual('family')
        self._resultado_preview = ctk.CTkTextbox(
            right, height=140, corner_radius=8, font=ctk.CTkFont(family=fixed, size=12),
            fg_color=colors.SIDEBAR_BG, border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR, text_color=colors.TEXT_COLOR, wrap='char',
        )
        self._resultado_preview._y_scrollbar.configure(height=120)
        self._resultado_preview._textbox.configure(exportselection=False)
        self._resultado_preview._textbox.bind('<<Copy>>', self._copiar_desde_preview)
        self._resultado_preview.grid(row=7, column=0, padx=16, sticky='nsew')
        self._lbl_abbreviated = self._text_label(right, t('lqip_abbreviated'), muted=True, wraplength=500)
        self._lbl_abbreviated.grid(row=8, column=0, padx=16, pady=(4, 0), sticky='ew')
        self._lbl_abbreviated.grid_forget()
        actions = ctk.CTkFrame(right, fg_color='transparent')
        actions.grid(row=9, column=0, padx=16, pady=(12, 16), sticky='ew')
        actions.grid_columnconfigure((0, 1), weight=1, uniform='actions')
        self._btn_copiar = self._action_button(actions, 'lqip_btn_copy', self._copiar)
        self._btn_copiar.grid(row=0, column=0, padx=(0, 4), sticky='ew')
        self._btn_guardar = self._action_button(actions, 'lqip_btn_save', self._guardar)
        self._btn_guardar.grid(row=0, column=1, padx=(4, 0), sticky='ew')
        left.bind('<Configure>', self._ajustar_textos, add='+')
        right.bind('<Configure>', self._ajustar_textos, add='+')
        self._actualizar_codigo()

    def _campo_numerico(self, parent, row, title, help_key, variable):
        self._text_label(parent, t(title)).grid(row=row, column=0, sticky='w')
        entry = ctk.CTkEntry(
            parent, textvariable=variable, width=80, font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG, border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
        )
        entry.grid(row=row, column=1, sticky='e')
        help_label = self._text_label(parent, t(help_key), muted=True, wraplength=330)
        help_label.grid(row=row + 1, column=0, columnspan=2, sticky='ew', pady=(0, 6))
        self._left_help_labels.append(help_label)
        error = self._text_label(parent, '', muted=False, wraplength=330)
        self._left_help_labels.append(error)
        error.grid(row=row + 2, column=0, columnspan=2, sticky='w', pady=(0, 4))
        error.grid_forget()
        return entry, error

    def _calidad(self, parent, row, variable, maximum):
        self._text_label(parent, t('lqip_quality')).grid(row=row, column=0, sticky='w')
        value = self._text_label(parent, str(variable.get()))
        value.grid(row=row, column=1, sticky='e')
        slider = ctk.CTkSlider(
            parent, from_=10, to=maximum, number_of_steps=maximum - 10, variable=variable,
            button_color=colors.ACENTO, button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO, fg_color=colors.SIDEBAR_SEPARATOR,
        )
        slider.grid(row=row + 1, column=0, columnspan=2, pady=(2, 0), sticky='ew')
        help_label = self._text_label(parent, t('lqip_quality_help'), muted=True, wraplength=330)
        help_label.grid(row=row + 2, column=0, columnspan=2, sticky='ew', pady=(0, 2))
        self._left_help_labels.append(help_label)
        return value

    def _preview_card(self, column, title):
        card = ctk.CTkFrame(self._comparison, fg_color=colors.SIDEBAR_BG, corner_radius=8)
        card.grid(row=0, column=column, padx=(0, 4) if column == 0 else (4, 0), sticky='nsew')
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        self._text_label(card, t(title), muted=True).grid(row=0, column=0, padx=10, pady=(6, 0), sticky='w')
        label = ctk.CTkLabel(
            card, text=t('lqip_select_hint') if column == 0 else t('lqip_generate_hint'),
            width=1, height=1, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            wraplength=220,
        )
        label.grid(row=1, column=0, padx=10, pady=4, sticky='nsew')
        meta = self._text_label(card, '—', muted=True)
        meta.grid(row=2, column=0, padx=10, pady=(0, 6), sticky='w')
        return label, meta

    def _action_button(self, parent, key, command):
        return ctk.CTkButton(
            parent, text=t(key), height=36, font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG, hover_color=colors.SIDEBAR_HOVER,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR, command=command,
        )

    def _ajustar_textos(self, event=None):
        scale = self._get_widget_scaling()
        if event is not None and event.widget is self._left:
            width = max(120, int(event.width / scale) - 32)
            self._lbl_descripcion.configure(wraplength=width)
            self._lbl_input_name.configure(wraplength=width)
            self._lbl_input_meta.configure(wraplength=width)
            for label in self._left_help_labels:
                label.configure(wraplength=width)
        elif event is not None and event.widget is self._right:
            width = max(120, int(event.width / scale) - 32)
            for label in (self._lbl_format_help, self._lbl_abbreviated, self._lbl_result_status, self._lbl_result_name):
                label.configure(wraplength=width)
        self._schedule_viewport_sync()

    def _cambiar_modo(self, label):
        self._modo_visible.set(label)
        self._state.modo.set(self._modo_a_interno[label])
        self._lqip_options.grid_forget()
        self._b64_options.grid_forget()
        is_lqip = self._state.modo.get() == 'lqip'
        (self._lqip_options if is_lqip else self._b64_options).grid(row=0, column=0, sticky='ew')
        self._lbl_descripcion.configure(text=t('lqip_mode_lqip_desc' if is_lqip else 'lqip_mode_b64_desc'))
        self._schedule_viewport_sync()

    def _actualizar_validacion(self):
        errors = self._state.errores_validacion()
        for field, entry, label, row in (
            ('ancho', self._entry_width, self._error_width, 2),
            ('blur', self._entry_blur, self._error_blur, 5),
        ):
            entry.configure(border_color=colors.ACENTO if field in errors else colors.SIDEBAR_SEPARATOR)
            if field in errors:
                label.configure(text=t(errors[field]))
                label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(0, 4))
            else:
                label.grid_forget()
        self._lbl_cal_lqip.configure(text=str(self._state.calidad_lqip.get()))
        self._lbl_cal_b64.configure(text=str(self._state.calidad_b64.get()))
        self._schedule_viewport_sync()
        return not errors

    def _ajustes_cambiados(self, *_):
        if self._resetting:
            return
        had_results = bool(self._results)
        self._revision += 1
        self._results.clear()
        self._state.resultados = []
        self._actualizar_validacion()
        self._render_selected()
        self._actualizar_acciones()
        if had_results or self._busy:
            self._lbl_info.configure(text=t('lqip_changed'))

    def _cargar_imagenes(self, rutas):
        """Reemplaza la única entrada y reinicia los controles sin callbacks intermedios."""
        rutas = tuple(rutas)
        if len(rutas) > 1:
            raise ValueError('LQIP / Base64 accepts one image at a time')
        self._revision += 1
        self._source_revision += 1
        self._imagenes = list(rutas)
        self._state.imagenes = list(self._imagenes)
        self._state.resultados = []
        self._results.clear()
        self._sources.clear()
        self._resetting = True
        try:
            self._state.restablecer_ajustes()
            self._cambiar_modo(t('lqip_mode_lqip'))
            self._campo_export.set(t('lqip_field_data_uri'))
        finally:
            self._resetting = False
        self._selected_index = 0 if self._imagenes else None
        self._actualizar_validacion()
        self._render_selected()
        self._actualizar_acciones()
        self._lbl_info.configure(text=t('lqip_loaded') if rutas else '')
        revision = self._source_revision
        paths = tuple(self._imagenes)
        queue = self._source_queue

        def load():
            for index, path in enumerate(paths):
                queue.put((revision, cargar_original(index, path)))

        if paths:
            Thread(target=load, daemon=True).start()

    def _recibir_originales(self):
        self._source_job = None
        try:
            while True:
                revision, source = self._source_queue.get_nowait()
                if revision != self._source_revision:
                    continue
                self._sources[source.index] = source
                if source.index == self._selected_index:
                    self._render_selected()
        except Empty:
            pass
        self._source_job = self.after(40, self._recibir_originales)

    def _programar_render(self, _event=None):
        if self._ui_ready and self._render_job is None:
            self._render_job = self.after_idle(self._render_selected)

    def _imagen_preview(self, label, image, placeholder, key):
        if image is None:
            label.configure(image=None)
            # CTkLabel deja la imagen nativa anterior al configurar image=None.
            label._label.configure(image='')
            self._display_images.pop(key, None)
            label.configure(text=placeholder)
            return
        scale = self._get_widget_scaling()
        width = max(1, int(label.winfo_width() / scale))
        height = max(1, int(label.winfo_height() / scale))
        ratio = min(width / image.width, height / image.height)
        size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
        rendered = image.resize(size, Image.Resampling.BILINEAR)
        tkimage = ctk.CTkImage(light_image=rendered, dark_image=rendered, size=size)
        # Mantener viva la imagen anterior hasta reemplazarla en el widget.
        label.configure(image=tkimage)
        self._display_images[key] = tkimage
        label.configure(text='')

    def _render_selected(self):
        if self._render_job is not None:
            self.after_cancel(self._render_job)
        self._render_job = None
        if not self._ui_ready:
            return
        index = self._selected_index
        source = self._sources.get(index) if index is not None else None
        item = self._results.get(index) if index is not None else None
        name = Path(self._imagenes[index]).name if index is not None else t('lqip_result')
        self._lbl_result_name.configure(text=name)
        self._lbl_input_name.configure(text=name if index is not None else t('lqip_select_hint'))
        if source and source.error:
            input_meta = t('lqip_item_error') + ': ' + source.error
        elif source and source.dimensions:
            w, h = source.dimensions
            input_meta = f'{w} × {h} px · {source.format} · {_peso(source.size)}'
        else:
            input_meta = t('lqip_loading') if index is not None else '—'
        self._lbl_input_meta.configure(text=input_meta)
        if item and item.error:
            status = t('lqip_item_error') + ': ' + item.error
        elif item and item.result:
            status = t('lqip_result_ready')
        else:
            status = t('lqip_generate_hint') if index is not None else t('lqip_select_hint')
        self._lbl_result_status.configure(text=status)
        original_image = source.image if source else None
        output_image = item.image if item else None
        if source and source.error:
            original_hint = t('lqip_item_error')
        else:
            original_hint = t('lqip_loading') if index is not None else t('lqip_select_hint')
        self._imagen_preview(self._original_label, original_image, original_hint, 'original')
        self._imagen_preview(self._output_label, output_image, t('lqip_generate_hint'), 'output')
        if source and source.dimensions:
            w, h = source.dimensions
            self._original_meta.configure(text=f'{w} × {h} px · {source.format}\n{_peso(source.size)}')
        else:
            self._original_meta.configure(text=t('lqip_item_error') if source and source.error else '—')
        if item and item.dimensions:
            w, h = item.dimensions
            self._output_meta.configure(text=f'{w} × {h} px · JPEG\n{_peso(item.jpeg_bytes)}')
            self._lbl_metrics.configure(text=f'Data URI: {_peso(item.uri_bytes)} · image/jpeg')
        else:
            self._output_meta.configure(text='—')
            self._lbl_metrics.configure(text=t('lqip_metrics_hint'))
        self._actualizar_codigo()

    def _obtener_clave_campo(self):
        return self._campo_a_clave[self._campo_export.get()]

    def _codigo_seleccionado(self):
        item = self._results.get(self._selected_index) if self._selected_index is not None else None
        return item.result[self._obtener_clave_campo()] if item and item.result else ''

    def _actualizar_codigo(self):
        key = self._obtener_clave_campo()
        self._lbl_format_help.configure(text=t('lqip_help_' + key))
        content = self._codigo_seleccionado()
        self._resultado_preview.configure(state='normal')
        self._resultado_preview.delete('1.0', 'end')
        self._resultado_preview.insert('1.0', content[:CODE_PREVIEW_LIMIT] if content else t('lqip_code_hint'))
        self._resultado_preview.configure(state='disabled')
        if len(content) > CODE_PREVIEW_LIMIT:
            self._lbl_abbreviated.grid(row=8, column=0, padx=16, pady=(4, 0), sticky='ew')
        else:
            self._lbl_abbreviated.grid_forget()
        self._actualizar_acciones()
        self._schedule_viewport_sync()

    def _actualizar_acciones(self):
        if not hasattr(self, '_btn_guardar'):
            return
        item = self._results.get(self._selected_index) if self._selected_index is not None else None
        self._btn_copiar.configure(state='normal' if item and item.result else 'disabled')
        self._btn_guardar.configure(state='normal' if self._state.resultados else 'disabled')
        self._btn_procesar.configure(
            state='normal' if self._imagenes and not self._busy and not self._state.errores_validacion() else 'disabled',
            text=t('processing') if self._busy else t('lqip_btn_process'),
        )

    def _procesar(self):
        if self._busy or not self._imagenes or not self._actualizar_validacion():
            return
        paths = tuple(self._imagenes)
        options = dict(self._state.obtener_opciones())
        revision = self._revision
        self._busy = True
        self._actualizar_acciones()
        self._lbl_info.configure(text=t('processing'))
        started = operations.submit(
            self, 'lqip', lambda: procesar_archivos(paths, options),
            lambda items: self._finalizar(revision, items),
            lambda error: self._fallo_generacion(revision, error),
        )
        if not started:
            self._busy = False
            self._actualizar_acciones()
            self._lbl_info.configure(text=t('lqip_busy'))

    def _finalizar(self, revision, items):
        self._busy = False
        if revision == self._revision:
            items = [item for item in items if item.index == 0 and self._imagenes and item.path == self._imagenes[0]][:1]
            self._results = {item.index: item for item in items}
            self._state.resultados = [item.result for item in items if item.result is not None]
            self._lbl_info.configure(text=t('lqip_result_ready') if self._state.resultados else t('lqip_item_error'))
            self._render_selected()
        self._actualizar_acciones()

    def _fallo_generacion(self, revision, error):
        self._busy = False
        if revision == self._revision:
            self._lbl_info.configure(text=f'{t("lqip_item_error")}: {error}')
        self._actualizar_acciones()

    def _copiar(self):
        content = self._codigo_seleccionado()
        if not content:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(content)
            copied = self.clipboard_get()
            # Windows puede convertir LF a CRLF al transferir texto.
            if copied.replace('\r\n', '\n') != content.replace('\r\n', '\n'):
                self._lbl_info.configure(text=t('lqip_copy_failed'))
                return
        except TclError:
            self._lbl_info.configure(text=t('lqip_copy_failed'))
            return
        self._lbl_info.configure(text=t('lqip_copied_full').format(count=len(content)))

    def _copiar_desde_preview(self, _event=None):
        """Copiar toda la vista abreviada entrega el código original completo."""
        textbox = self._resultado_preview._textbox
        ranges = textbox.tag_ranges('sel')
        if (
            len(self._codigo_seleccionado()) > CODE_PREVIEW_LIMIT
            and len(ranges) == 2
            and textbox.compare(ranges[0], '==', '1.0')
            and textbox.compare(ranges[1], '>=', 'end-1c')
        ):
            self._copiar()
            return 'break'
        return None

    def _guardar(self):
        if not self._state.resultados:
            return
        path = filedialog.asksaveasfilename(
            title=t('lqip_save_title'), defaultextension='.txt',
            initialfile=Path(self._imagenes[0]).stem + '_lqip',
            filetypes=[(t('file_txt'), '*.txt'), (t('file_json'), '*.json')],
        )
        if not path:
            return
        try:
            if Path(path).suffix.lower() == '.json':
                exportar_json(self._state.resultados, path)
            else:
                exportar_txt(self._state.resultados, path, campo=self._obtener_clave_campo())
            self._lbl_info.configure(text=f'{t("lqip_saved_as")} {Path(path).name}')
        except OSError as error:
            self._lbl_info.configure(text=f'{t("error_generic")}: {error}')

    def _limpiar(self):
        self._cargar_imagenes([])
        self._lbl_info.configure(text='')

    def destroy(self):
        self._revision += 1
        self._source_revision += 1
        for job in (self._source_job, self._render_job):
            if job is not None:
                self.after_cancel(job)
        for variable, token in self._traces:
            variable.trace_remove('write', token)
        super().destroy()
