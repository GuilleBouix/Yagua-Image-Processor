"""Collection controller. Workers return plain data; Tk stays on the UI thread."""
from __future__ import annotations

from itertools import count
import logging
from pathlib import Path
from queue import Empty, PriorityQueue
from threading import Event, Lock, Thread
import sys
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk
from PIL import Image, ImageTk

from app.modules.compress import formatear_bytes
from app.modules.metadata_batch import (
    MetadataDraft, MetadataTask, exportar_lote, leer_archivo, preparar_borrador, procesar_lote,
)
from app.translations import t
from app.ui import colors, fonts, styles
from app.ui.frames.metadata.state import path_key
from app.ui.operations import operations
from app.utils.paths import resource_path
from app.ui.image_cache import image_cache
from app.ui.rendering import activate_tab, configure_changed


logger = logging.getLogger(__name__)


ERROR_KEYS = {
    'invalid_date': 'invalid_date_format', 'invalid_number': 'invalid_metadata_number',
    'invalid_option': 'invalid_metadata_option', 'invalid_gps': 'invalid_gps',
    'gps_pair': 'gps_pair_required', 'gps_conflict': 'gps_clear_conflict',
    'sync_requires_date': 'sync_date_required', 'invalid_orientation': 'invalid_orientation',
    'empty': 'no_metadata_changes',
    'source_changed': 'meta_source_changed', 'error': 'error_saving',
    'invalid_field': 'invalid_metadata_option', 'output_folder_required': 'select_output_folder_clean',
}


def error_text(error: str) -> str:
    return t(ERROR_KEYS.get(error, error))


def decode_preview(path: str, bound: int = 1024) -> Image.Image:
    return image_cache.load(path, (bound, bound)).image


class MetadataCollection:
    def __init__(self, view):
        self.view: Any = view
        self.epoch = 0
        self.revision = 0
        self.queue: PriorityQueue = PriorityQueue()
        self.sequence = count()
        self.closed = Event()
        self.io_lock = Lock()
        self.worker: Thread | None = None
        self.form_key: str | None = None
        self.preview: Image.Image | None = None
        self.preview_error = ''
        self.preview_token = None
        self.visible = True
        self.summary = ''
        self.details_expanded = False
        self.notice = ''
        self.feedback = ''
        self.tab = ''
        self._thumb_requests = set()

    @property
    def state(self):
        return self.view._state

    def refresh(self, *, rebuild=False, key=None):
        for files in self.view._file_views:
            files.active_view = self.visible and files.tab_frame is self.view._frames.get(self.tab)
            if rebuild:
                files.rebuild()
            else:
                files.refresh(key)
        if not operations.is_busy() and hasattr(self.view, '_btn_guardar_edit'):
            current = self.state.current
            editable = bool(current and current.data and current.data['editable'] and not current.data['edit_error'])
            for button, enabled in (
                (self.view._btn_guardar_edit, editable or bool(self.state.marked)),
                (self.view._btn_apply_fields, editable and bool(self.state.marked)),
                (self.view._btn_limpiar_exif, bool(self.state.marked)),
            ):
                configure_changed(button, state='normal' if enabled else 'disabled')
        if not operations.is_busy():
            self.view._sync_presentation()

    def request_thumbnail(self, key):
        token = (self.epoch, key)
        if token not in self._thumb_requests:
            self._thumb_requests.add(token)
            self.enqueue('thumb', key)

    def enqueue(self, kind, key):
        self.queue.put((0 if kind == 'active' else 1, next(self.sequence),
                        kind, self.epoch, self.revision, key))
        if self.worker is None:
            self.worker = Thread(target=self._worker, daemon=True, name='yagua-metadata-reader')
            self.worker.start()

    def _worker(self):
        while not self.closed.is_set():
            try:
                _, _, kind, epoch, revision, key = self.queue.get(timeout=.2)
            except Empty:
                continue
            if epoch != self.epoch or (kind == 'active' and revision != self.revision):
                continue
            # Paths are copied into the queue key, never obtained from a Tk widget.
            path = key
            if kind == 'thumb':
                try:
                    with self.io_lock:
                        reduced = image_cache.load(path, (44, 44))
                        thumb, fmt, size_bytes = reduced.image, reduced.format, reduced.bytes
                    result = (thumb, fmt, size_bytes)
                except Exception:
                    result = (None, '', 0)
                self.view._post_ui(0, lambda e=epoch, k=key, r=result: self._thumbnail(e, k, r))
            else:
                data, read_error, preview, preview_error = None, '', None, ''
                with self.io_lock:
                    try:
                        data = leer_archivo(path)
                    except Exception as error:
                        read_error = str(error)
                    try:
                        preview = decode_preview(path)
                    except Exception as error:
                        preview_error = str(error)
                result = (data, read_error, preview, preview_error)
                self.view._post_ui(0, lambda e=epoch, rev=revision, k=key, r=result: self.loaded(e, rev, k, r))

    def _thumbnail(self, epoch, key, result):
        item = self.state.items.get(key)
        if epoch != self.epoch or item is None:
            return
        thumb, fmt, size_bytes = result
        if thumb is not None:
            item.thumbnail = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
            item.format, item.size_bytes = fmt, size_bytes
        self.refresh(key=key)

    def add(self, paths):
        if self.view._operation_blocked(global_job=True):
            return
        self.capture()
        added, excluded, duplicates = self.state.add(list(paths))
        self.feedback = ''
        notices = []
        if len(self.state.items) == self.state.limit:
            notices.append(t('meta_limit_notice').format(limit=self.state.limit))
        if excluded:
            notices.append(t('meta_excluded_notice').format(count=excluded))
        if duplicates:
            notices.append(t('meta_duplicates_notice').format(count=duplicates))
        self.notice = ' · '.join(notices)
        self.refresh(rebuild=True)
        if self.state.active is None and added:
            self.activate(added[0], preserve_notice=True)
        self.view._lbl_info.configure(text=self.notice)

    def explore(self):
        if self.view._operation_blocked(global_job=True):
            return
        paths = filedialog.askopenfilenames(parent=self.view, title=t('meta_add_images'),
            filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic *.heif')])
        if paths:
            self.add(paths)

    def mark(self, key, checked):
        if not self.view._operation_blocked(global_job=True):
            self.state.items[key].checked = checked
        self.refresh()

    def mark_all(self, checked):
        if not self.view._operation_blocked(global_job=True):
            for item in self.state.items.values():
                item.checked = checked
        self.refresh()

    def capture(self):
        item = self.state.items.get(self.form_key or '')
        if item is None or item.data is None or not item.data['editable'] or item.data['edit_error']:
            return
        values = self.form_values()
        base = item.data['values']
        item.draft = MetadataDraft({key: value for key, value in values.items() if value != str(base.get(key, ''))},
            self.view._sync_dates_var.get(), self.view._clear_gps_var.get(),
            self.view._orientacion_values.get(self.view._combo_orientacion.get()))

    def form_values(self):
        return {key: self.view._enum_values[key].get(widget.get(), '') if key in self.view._enum_values
                else widget.get().strip() for key, widget in self.view._campos_edit.items()}

    def activate(self, key, *, force=False, preserve_notice=False):
        if self.view._operation_blocked(global_job=True):
            return
        if key not in self.state.items:
            return
        current = self.state.current
        if key == self.state.active and not force and current and current.data and self.preview is not None and not current.data['edit_error']:
            return
        self.capture()
        if not preserve_notice:
            self.notice = ''
        if not force:
            self.feedback = ''
        self.revision += 1
        self.state.active = key
        item = self.state.items[key]
        if item.status == 'meta_read_error':
            self._thumb_requests.discard((self.epoch, key))
        self.state.ruta = item.path
        self.state.ruta_edicion = None
        self.form_key = None
        self.preview = None
        self.preview_token = None
        self.preview_error = ''
        self.view._state.metadatos = {}
        self.view._renderizar_metadatos({})
        for widget in [*self.view._campos_edit.values(), self.view._combo_orientacion,
                       self.view._sync_dates_check, self.view._clear_gps_check]:
            configure_changed(widget, state='disabled')
        self.refresh()
        self.view._lbl_info.configure(text=t('reading_metadata'))
        self.render_previews(placeholder=t('reading_metadata'))
        self.enqueue('active', key)

    def loaded(self, epoch, revision, key, result):
        if self.closed.is_set() or epoch != self.epoch or revision != self.revision or key != self.state.active:
            return
        if operations.is_busy():
            self.view.after(50, lambda: self.loaded(epoch, revision, key, result))
            return
        data, error, self.preview, preview_error = result
        self.preview_token = (epoch, revision, key)
        item = self.state.items[key]
        item.data = data
        self.preview_error = t('meta_preview_error') + ': ' + preview_error if preview_error else ''
        if data is None:
            item.status, item.detail = 'meta_read_error', error_text(error)
            self.state.metadatos = {}
            self.view._renderizar_metadatos({})
            self.view._meta_empty.configure(text=t('meta_read_error'))
            self.view._lbl_info.configure(text=t('meta_read_error') + ': ' + error_text(error))
            self.set_form({}, enabled=False)
        else:
            item.format, item.size_bytes = data['format'], data['bytes']
            if item.status in ('meta_pending', 'meta_read_error', 'meta_ready', 'meta_no_exif'):
                item.status = 'meta_ready' if data['metadata'] else 'meta_no_exif'
                item.detail = ''
            enabled = data['editable'] and not data['edit_error']
            self.state.ruta_edicion = item.path if enabled else None
            self.set_form({**data['values'], **item.draft.values}, enabled=enabled)
            self.form_key = key if enabled else None
            if enabled:
                self.view._sync_dates_var.set(item.draft.sync_dates)
                self.view._clear_gps_var.set(item.draft.clear_gps)
                label = next((label for label, value in self.view._orientacion_values.items()
                              if value == item.draft.orientation), t('keep_orientation'))
                self.view._combo_orientacion.set(label)
            else:
                self.view._info_tecnica.configure(text=t('meta_read_only') if not data['edit_error'] else error_text(data['edit_error']))
            self.view._aplicar_metadatos(data['metadata'])
            self.view._lbl_info.configure(text=self.notice or (
                self.feedback if self.tab != t('clean_batch') else ''))
        self.render_previews()
        self.refresh()

    def set_form(self, values, *, enabled):
        for widget in self.view._campos_edit.values():
            configure_changed(widget, state='readonly' if isinstance(widget, ctk.CTkComboBox) else 'normal')
        self.view._aplicar_campos_edit(values)
        for widget in [*self.view._campos_edit.values(), self.view._combo_orientacion,
                       self.view._sync_dates_check, self.view._clear_gps_check]:
            configure_changed(widget, state=('readonly' if isinstance(widget, ctk.CTkComboBox) else 'normal') if enabled else 'disabled')

    def render_previews(self, placeholder=''):
        item = self.state.current
        ready = self.preview_token == (self.epoch, self.revision, self.state.active)
        data = item.data if item and ready else None
        info = ''
        if data:
            width, height = data['size']
            info = f'{width} × {height} px · {data["format"]} · {formatear_bytes(data["bytes"])}'
        for pane in self.view._previews:
            active = bool(item) and self.visible and pane.tab_frame is self.view._frames.get(self.tab)
            pane.set_visible(active)
            if item is None or active:
                hint = placeholder or (self.preview_error if ready else t('reading_metadata') if item else '')
                pane.show(item.path if item else '', self.preview if ready else None, info, hint)
        configure_changed(self.view._edit_target, text=Path(item.path).name if item else t('meta_current'))

    def change_tab(self, tab):
        self.capture()
        self.tab = tab
        for pane in self.view._previews:
            pane.set_visible(False)
        activate_tab(self.view._frames, tab)
        current = self.state.current
        if tab == t('view') and current and current.data and self.preview_token == (self.epoch, self.revision, self.state.active):
            self.view._aplicar_metadatos(current.data['metadata'])
        self.refresh()
        self.render_previews()
        if self.summary and tab == t('clean_batch'):
            self.view._lbl_info.configure(text='')
        elif self.feedback:
            self.view._lbl_info.configure(text=self.feedback)

    def toggle_details(self):
        self.details_expanded = not self.details_expanded
        self.view._sync_presentation()

    def _dialog(self, title, width, height):
        dialog = ctk.CTkToplevel(self.view)
        self._dialog_icon(dialog)
        if sys.platform == 'win32':
            # CTk installs its own Windows icon after 200 ms; restore Yagua's.
            dialog.after(250, lambda: self._dialog_icon(dialog) if dialog.winfo_exists() else None)
        dialog.title(t(title))
        dialog.configure(fg_color=styles.palette().background)
        dialog.geometry(f'{width}x{height}')
        dialog.transient(self.view.winfo_toplevel())
        dialog.grid_columnconfigure(0, weight=1)
        dialog.bind('<Escape>', lambda _event: dialog.destroy())
        dialog.after_idle(lambda: (dialog.lift(), dialog.grab_set()))
        return dialog

    @staticmethod
    def _dialog_icon(dialog):
        try:
            ico = resource_path('assets/icon.ico')
            if sys.platform == 'win32' and ico.exists():
                dialog.iconbitmap(str(ico))
            else:
                with Image.open(resource_path('assets/icon.png')) as image:
                    photo = ImageTk.PhotoImage(image.convert('RGBA'), master=dialog)
                dialog.iconphoto(False, photo)
                dialog._yagua_icon = photo
        except Exception:
            logger.warning('No se pudo aplicar el icono de Yagua al diálogo', exc_info=True)

    def _dialog_button(self, parent, key, command, *, primary=False):
        return styles.Button(parent, role='primary' if primary else 'secondary',
            text=t(key), command=command, height=40, width=1, font=fonts.FUENTE_BASE)

    def destination(self, count_items, *, choose_scope=False) -> 'Any':
        from app.ui.saving import mode
        overwrite = mode(self.view) == 'overwrite'
        if not choose_scope:
            folder = None if overwrite else filedialog.askdirectory(parent=self.view, title=t('select_output_folder_clean'))
            return (overwrite, folder) if overwrite or folder else None
        dialog = self._dialog('meta_save', 540, 290)
        dialog.minsize(500, 290)
        scope = ctk.StringVar(value='current' if self.state.current else 'marked')
        palette = styles.palette()
        row_offset = 0
        if choose_scope:
            ctk.CTkLabel(dialog, text=t('meta_save_scope'), font=fonts.FUENTE_BASE, anchor='w').grid(
                row=0, column=0, padx=20, pady=(16, 4), sticky='ew')
            for row, (value, key) in enumerate((('current', 'meta_current'), ('marked', 'meta_marked')), 1):
                enabled = bool(self.state.current) if value == 'current' else bool(self.state.marked)
                ctk.CTkRadioButton(dialog, text=t(key), variable=scope, value=value,
                    state='normal' if enabled else 'disabled', font=fonts.FUENTE_BASE,
                    fg_color=palette.primary, hover_color=palette.primary_hover,
                    border_color=palette.border, text_color=palette.text,
                    text_color_disabled=palette.muted).grid(
                        row=row, column=0, padx=20, pady=8, sticky='w')
            row_offset = 3
        count_label = ctk.CTkLabel(dialog, text=t('meta_destination_count').format(count=count_items),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, wraplength=480, justify='left')
        count_label.grid(row=row_offset, column=0, padx=20, pady=(12, 8), sticky='w')
        def update_count(*_args):
            count_label.configure(text=t('meta_destination_count').format(
                count=len(self.state.marked) if scope.get() == 'marked' else int(self.state.current is not None)))
        if choose_scope:
            scope.trace_add('write', update_count)
            update_count()
        result = []
        def accept():
            count = (len(self.state.marked) if scope.get() == 'marked' else int(self.state.current is not None)) if choose_scope else count_items
            if not count:
                return
            if choose_scope:
                items = self.state.marked if scope.get() == 'marked' else [self.state.current]
                if not any(item and item.draft.dirty for item in items):
                    count_label.configure(text=t('no_metadata_changes'))
                    return
                if scope.get() == 'current':
                    item = self.state.current
                    if item is None or item.data is None or not item.data['editable'] or item.data['edit_error']:
                        count_label.configure(text=t('meta_read_only'))
                        return
                    _, error = preparar_borrador(item.data['values'], item.draft)
                    if error:
                        count_label.configure(text=error_text(error))
                        return
            folder = None if overwrite else filedialog.askdirectory(parent=dialog, title=t('select_output_folder_clean'))
            if not overwrite and not folder:
                return
            result.append((scope.get() == 'marked', overwrite, folder) if choose_scope else (overwrite, folder))
            dialog.destroy()
        actions = ctk.CTkFrame(dialog, fg_color='transparent')
        actions.grid(row=row_offset + 1, column=0, padx=20, pady=(16, 20), sticky='ew')
        actions.grid_columnconfigure((0, 1), weight=1)
        self._dialog_button(actions, 'meta_cancel', dialog.destroy).grid(row=0, column=0, padx=(0, 6), sticky='ew')
        self._dialog_button(actions, 'meta_continue', accept, primary=True).grid(row=0, column=1, padx=(6, 0), sticky='ew')
        self.view.wait_window(dialog)
        return result[0] if result else None

    def save(self, *, selected: bool | None = False, clean=False):
        if self.view._operation_blocked(global_job=True):
            return
        self.capture()
        destination = None
        if selected is None:
            if not self.state.current and not self.state.marked:
                self.view._lbl_info.configure(text=t('meta_no_selection'))
                return
            if not any(item.draft.dirty for item in self.state.items.values()):
                self.view._lbl_info.configure(text=t('no_metadata_changes'))
                return
            chosen = self.destination(1, choose_scope=True)
            if chosen is None:
                return
            selected, overwrite, folder = chosen
            destination = (overwrite, folder)
        items = self.state.marked if selected else ([self.state.current] if self.state.current else [])
        if not items:
            self.view._lbl_info.configure(text=t('meta_no_selection'))
            return
        if not clean and selected and not any(item.draft.dirty for item in items):
            self.view._lbl_info.configure(text=t('no_metadata_changes'))
            return
        if not clean and not selected:
            item = items[0]
            if item.data is None or not item.data['editable'] or item.data['edit_error']:
                self.view._lbl_info.configure(text=t('meta_read_only'))
                return
            _, error = preparar_borrador(item.data['values'], item.draft)
            if error:
                self.view._lbl_info.configure(text=error_text(error))
                return
        tasks = tuple(MetadataTask(item.path, item.draft.copy(),
                                   item.data['fingerprint'] if item.data else None) for item in items)
        if destination is None:
            destination = self.destination(len(tasks))
        if destination is None:
            return
        overwrite, folder = destination
        def start(_folder, plan):
            self.epoch += 1
            self._thumb_requests.clear()
            self.revision += 1
            self.view._lbl_info.configure(text=t('processing'))
            def work():
                with self.io_lock:
                    return procesar_lote(tasks, clean=clean, overwrite=overwrite,
                                         folder=_folder, output_policy=plan)
            self.view._submit_job(work, on_success=lambda result: self.finished(result, overwrite))
        self.view._prepare_save(tuple(task.path for task in tasks), None, start, folder=folder,
                                notice=t('meta_clean_confirm') if clean else '')

    def finished(self, result, overwrite):
        lines = []
        for row in result['items']:
            item = self.state.items.get(path_key(row['ruta']))
            if item is None:
                continue
            status = row['estado']
            item.status = {'saved': 'meta_saved' if overwrite else 'meta_copied',
                           'unchanged': 'no_metadata_changes', 'unsupported': 'meta_read_only', 'error': 'error_generic'}[status]
            item.detail = row['destino'] if status == 'saved' else error_text(row['error'])
            lines.append(f'{item.path}\n{t(item.status)}: {item.detail}')
            if status == 'saved' and overwrite:
                image_cache.invalidate(item.path)
                item.data = None
                item.draft = MetadataDraft()
                item.thumbnail = None
                self.enqueue('thumb', path_key(item.path))
        self.summary = t('meta_result').format(ok=result['ok'], unchanged=result['unchanged'], errors=result['errores'])
        self.feedback = self.summary
        self.details_expanded = False
        self.view._summary.configure(state='normal')
        self.view._summary.delete('1.0', 'end')
        self.view._summary.insert('1.0', '\n\n'.join(lines))
        self.view._summary.configure(state='disabled')
        if overwrite:
            self.form_key = None  # Do not capture the stale form over successful writes.
        self.refresh()
        if self.state.active:
            self.activate(self.state.active, force=True)
        self.view._lbl_info.configure(text='' if self.tab == t('clean_batch') else self.summary)

    def apply_fields(self, fields, options=None):
        self.capture()
        for item in self.state.marked:
            for key, value in fields.items():
                if value:
                    item.draft.values[key] = value
            for key, value in (options or {}).items():
                setattr(item.draft, key, value)
        current = self.state.current
        if current and current.checked and current.data and self.form_key == self.state.active:
            draft = current.draft
            self.set_form({**current.data['values'], **draft.values}, enabled=True)
            self.view._sync_dates_var.set(draft.sync_dates)
            self.view._clear_gps_var.set(draft.clear_gps)
            label = next((label for label, value in self.view._orientacion_values.items()
                          if value == draft.orientation), t('keep_orientation'))
            self.view._combo_orientacion.set(label)
        self.refresh()

    def choose_fields(self):
        if self.view._operation_blocked(global_job=True):
            return
        self.capture()
        item = self.state.current
        if not self.state.marked or item is None or item.data is None or not item.data['editable'] or item.data['edit_error']:
            self.view._lbl_info.configure(text=t('meta_no_selection'))
            return
        values = self.form_values()
        populated = sum(bool(value) for value in values.values())
        dialog = self._dialog('meta_copy_fields', 660, min(540, 290 + populated * 40))
        dialog.minsize(560, 340)
        dialog.grid_rowconfigure(4, weight=1)
        ctk.CTkLabel(dialog, text=Path(item.path).name, font=fonts.FUENTE_BASE,
            anchor='w', justify='left', wraplength=600).grid(
                row=0, column=0, padx=20, pady=(16, 4), sticky='ew')
        ctk.CTkLabel(dialog, text=t('meta_apply_help'), font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, wraplength=600, justify='left', anchor='w').grid(
                row=1, column=0, padx=20, pady=(0, 12), sticky='ew')
        query = ctk.StringVar()
        search = styles.Entry(dialog, textvariable=query, placeholder_text=t('meta_search_fields'),
            height=36, font=fonts.FUENTE_BASE)
        search.grid(row=2, column=0, padx=20, pady=(0, 8), sticky='ew')
        headings = ctk.CTkFrame(dialog, fg_color='transparent')
        headings.grid(row=3, column=0, padx=24, sticky='ew')
        headings.grid_columnconfigure((0, 1), weight=1, uniform='copy-fields')
        for column, key in enumerate(('meta_field', 'meta_value')):
            ctk.CTkLabel(headings, text=t(key), font=fonts.FUENTE_CHICA, anchor='w',
                         text_color=colors.TEXT_GRAY).grid(row=0, column=column, sticky='ew')
        body = ctk.CTkScrollableFrame(dialog, **styles.surface('list'), **styles.scrollbar())
        body._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        body.grid(row=4, column=0, padx=16, sticky='nsew')
        body.grid_columnconfigure(0, weight=1)
        choices = {}
        rows = []
        summary = ctk.CTkLabel(dialog, text='', font=fonts.FUENTE_CHICA,
                              text_color=colors.TEXT_GRAY, anchor='w')
        summary.grid(row=5, column=0, padx=20, pady=(8, 0), sticky='ew')
        actions = ctk.CTkFrame(dialog, fg_color='transparent')
        actions.grid(row=6, column=0, padx=20, pady=(8, 16), sticky='ew')
        actions.grid_columnconfigure((0, 1), weight=1)
        def update_summary(*_args):
            count = sum(variable.get() for variable in choices.values()) + sum(
                variable.get() for variable, _value in options.values())
            summary.configure(text=t('meta_copy_summary').format(fields=count, images=len(self.state.marked)))
            apply_button.configure(state='normal' if count else 'disabled')
        def add_row(label, value, variable):
            row = ctk.CTkFrame(body, fg_color='transparent')
            row.grid(row=len(rows), column=0, sticky='ew', pady=4)
            row.grid_columnconfigure((0, 1), weight=1, uniform='copy-fields')
            checkbox = styles.CheckBox(row, text=label, variable=variable, width=1,
                checkbox_width=18, checkbox_height=18, font=fonts.FUENTE_BASE)
            checkbox.grid(row=0, column=0, sticky='ew', padx=(0, 12), pady=4)
            preview = value[:120] + ('…' if len(value) > 120 else '')
            value_label = ctk.CTkLabel(row, text=preview, anchor='w', justify='left', width=1,
                wraplength=260, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY)
            value_label.grid(row=0, column=1, sticky='ew')
            def resize_row(event):
                half = int(event.width / dialog._get_widget_scaling()) // 2
                value_label.configure(wraplength=max(80, half - 8))
                if checkbox._text_label is not None:
                    checkbox._text_label.configure(wraplength=max(80, half - 44))
            row.bind('<Configure>', resize_row, add=True)
            rows.append((self.view._texto_busqueda(f'{label} {value}'), row))
            variable.trace_add('write', update_summary)
        from app.modules.metadata import CAMPOS_EDITABLES
        for key, value in values.items():
            if not value:
                continue
            variable = ctk.BooleanVar(value=bool(item.draft.values.get(key)))
            add_row(t(CAMPOS_EDITABLES[key]), value, variable)
            choices[key] = variable
        options = {}
        for key, label, value in (
            ('clear_gps', 'clear_gps', item.draft.clear_gps),
            ('sync_dates', 'sync_dates', item.draft.sync_dates),
            ('orientation', 'orientation_transform', item.draft.orientation),
        ):
            if value:
                variable = ctk.BooleanVar(value=True)
                display = next((name for name, code in self.view._orientacion_values.items()
                                if code == value), str(value)) if key == 'orientation' else t('apply_changes')
                add_row(t(label), display, variable)
                options[key] = (variable, value)
        def accept():
            selected = {key: values[key] for key, variable in choices.items() if variable.get()}
            flags = {key: value for key, (variable, value) in options.items() if variable.get()}
            self.apply_fields(selected, flags)
            dialog.destroy()
        self._dialog_button(actions, 'meta_cancel', dialog.destroy).grid(row=0, column=0, padx=(0, 6), sticky='ew')
        apply_button = self._dialog_button(actions, 'apply_changes', accept, primary=True)
        apply_button.grid(row=0, column=1, padx=(6, 0), sticky='ew')
        empty = ctk.CTkLabel(body, text=t('meta_no_matching_fields'), font=fonts.FUENTE_CHICA,
                             text_color=colors.TEXT_GRAY)
        empty.grid(row=len(rows), column=0, pady=16)
        def filter_rows(*_args):
            term = self.view._texto_busqueda(query.get().strip())
            visible = 0
            for text, row in rows:
                if term in text:
                    row.grid()
                    visible += 1
                else:
                    row.grid_remove()
            if visible:
                empty.grid_remove()
            else:
                empty.grid()
            body._parent_canvas.yview_moveto(0)
        query.trace_add('write', filter_rows)
        filter_rows()
        update_summary()
        search.focus_set()
        self.view.wait_window(dialog)

    def export(self, fmt):
        if self.view._operation_blocked(global_job=True):
            return
        batch = self.view._export_scope.get() == t('meta_marked')
        paths = tuple(item.path for item in self.state.marked) if batch else (
            (self.state.current.path,) if self.state.current else ())
        if not paths:
            self.view._lbl_info.configure(text=t('meta_no_selection'))
            return
        destination = filedialog.asksaveasfilename(parent=self.view, title=t('export_metadata'),
            defaultextension=f'.{fmt}', filetypes=[(fmt.upper(), f'*.{fmt}')], initialfile=f'metadatos.{fmt}')
        if not destination:
            return
        def work():
            with self.io_lock:
                if batch:
                    return exportar_lote(paths, destination, fmt)
                data = leer_archivo(paths[0])
                from app.modules.metadata import exportar_metadatos
                exportar_metadatos(data['metadata'], destination, fmt)
                return []
        def success(entries):
            for entry in entries:
                item = self.state.items.get(path_key(entry['ruta']))
                if item and entry['error']:
                    item.status, item.detail = 'meta_read_error', error_text(entry['error'])
            self.refresh()
            self.view._lbl_info.configure(text=f'{t("exported_as")} {Path(destination).name}')
        self.view._submit_job(work, on_success=success,
            on_error=lambda error: self.view._lbl_info.configure(text=f'{t("error_saving")}: {error}'))

    def clear(self):
        if self.view._operation_blocked(global_job=True):
            return
        self.capture()
        if any(item.draft.dirty for item in self.state.items.values()) and not messagebox.askyesno(
                t('metadata_title'), t('meta_discard_drafts'), parent=self.view):
            return
        self.epoch += 1
        self._thumb_requests.clear()
        self.revision += 1
        self.form_key = None
        self.state.clear()
        self.notice = self.summary = self.feedback = ''
        self.details_expanded = False
        self.view._edit_query.set('')
        self.view._edit_section.set(t('meta_all_sections'))
        self.view._filtrar_campos()
        self.view._panel_editar._parent_canvas.yview_moveto(0)
        self.preview, self.preview_error = None, ''
        self.preview_token = None
        self.set_form({}, enabled=False)
        self.view._info_tecnica.configure(text='')
        self.view._renderizar_metadatos({})
        self.render_previews()
        self.refresh(rebuild=True)
        self.view._summary.configure(state='normal')
        self.view._summary.delete('1.0', 'end')
        self.view._summary.configure(state='disabled')
        self.view._lbl_info.configure(text='')
