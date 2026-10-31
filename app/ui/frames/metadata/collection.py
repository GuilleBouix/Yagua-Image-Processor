"""Controlador del catálogo; los workers devuelven datos simples y Tk permanece en el hilo principal."""
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
from app.modules.metadata_containers import SUPPORTED_FORMATS
from app.utils.saving import canonical_format, plan_outputs
from app.modules.metadata_batch import (
    MetadataDraft, MetadataTask, combinar_formulario, exportar_lote, leer_archivo, preparar_borrador, procesar_lote,
)
from app.translations import t
from app.ui import colors, fonts, styles
from app.ui.frames.metadata.state import path_key
from app.ui.operations import operations
from app.ui.status import operation_summary
from app.ui.windows import center_on_parent
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
    'invalid_metadata_container': 'meta_read_error',
    'source_changed': 'meta_source_changed', 'error': 'error_saving',
    'invalid_field': 'invalid_metadata_option', 'output_folder_required': 'select_output_folder_clean',
}


def error_text(error: str) -> str:
    """Traduce un código de error del catálogo a texto de interfaz."""
    return t(ERROR_KEYS.get(error, error))


def decode_preview(path: str, bound: int = 1024) -> Image.Image:
    """Obtiene una imagen reducida desde la caché compartida."""
    return image_cache.load(path, (bound, bound)).image


class MetadataCollection:
    """Coordina workers, selección, formularios y guardado de metadatos."""
    def __init__(self, view):
        """Inicializa colas, revisiones y recursos de la vista EXIF."""
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
        """Devuelve el estado vigente para comprobar callbacks antiguos."""
        return self.view._state

    @staticmethod
    def compatible(item):
        """Unknown headers are checked by the worker; known unsupported files stay inert."""
        if item.data is not None:
            return item.data.get('writable', item.data['editable'])
        return not item.format or canonical_format(item.format) in SUPPORTED_FORMATS

    def refresh(self, *, rebuild=False, key=None):
        """Invalida trabajos asociados a una selección anterior."""
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
                (self.view._btn_guardar_edit, editable or any(i.draft.dirty and self.compatible(i) for i in self.state.marked)),
                (self.view._btn_limpiar_exif, any(self.compatible(i) for i in self.state.marked)),
            ):
                configure_changed(button, state='normal' if enabled else 'disabled')
        if not operations.is_busy():
            self.view._sync_presentation()
            current = self.state.current
            exportable = bool(current and current.data and current.data.get('supported', True) and not current.data.get('read_error'))
            for button in self.view._export_actions.winfo_children():
                configure_changed(button, state='normal' if exportable else 'disabled')

    def request_thumbnail(self, key):
        """Solicita una miniatura vinculada a la revisión actual."""
        token = (self.epoch, key)
        if token not in self._thumb_requests:
            self._thumb_requests.add(token)
            self.enqueue('thumb', key)

    def enqueue(self, kind, key):
        """Encola trabajo con prioridad sin acceder a widgets desde el worker."""
        self.queue.put((0 if kind == 'active' else 1, next(self.sequence),
                        kind, self.epoch, self.revision, key))
        if self.worker is None:
            self.worker = Thread(target=self._worker, daemon=True, name='yagua-metadata-reader')
            self.worker.start()

    def _worker(self):
        """Carga metadatos y miniaturas fuera de Tk para mantener fluida la interfaz."""
        while not self.closed.is_set():
            try:
                _, _, kind, epoch, revision, key = self.queue.get(timeout=.2)
            except Empty:
                continue
            if epoch != self.epoch or (kind == 'active' and revision != self.revision):
                continue
            # Las rutas se copian a la cola; el worker nunca las lee desde un widget Tk.
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
        """Decodifica y reduce una imagen para su miniatura de lista."""
        item = self.state.items.get(key)
        if epoch != self.epoch or item is None:
            return
        thumb, fmt, size_bytes = result
        if thumb is not None:
            item.thumbnail = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
            item.format, item.size_bytes = fmt, size_bytes
        self.refresh(key=key)

    def add(self, paths):
        """Agrega rutas válidas, conserva selección y comunica límites o duplicados."""
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
        """Abre el diálogo de archivos y agrega solo si el usuario confirma una selección."""
        if self.view._operation_blocked(global_job=True):
            return
        paths = filedialog.askopenfilenames(parent=self.view, title=t('meta_add_images'),
            filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic *.heif')])
        if paths:
            self.add(paths)

    def mark(self, key, checked):
        """Cambia la marca de un archivo cuando la operación lo permite."""
        if not self.view._operation_blocked(global_job=True):
            self.state.items[key].checked = checked
        self.refresh()

    def mark_all(self, checked):
        """Marca o desmarca todos los archivos del catálogo."""
        if not self.view._operation_blocked(global_job=True):
            for item in self.state.items.values():
                item.checked = checked
        self.refresh()

    def capture(self):
        """Guarda un borrador independiente del formulario del archivo activo."""
        item = self.state.items.get(self.form_key or '')
        if item is None or item.data is None or not item.data['editable'] or item.data['edit_error']:
            return
        values = self.form_values()
        base = item.data['values']
        item.draft = MetadataDraft({key: value for key, value in values.items() if value != str(base.get(key, ''))},
            self.view._sync_dates_var.get(), self.view._clear_gps_var.get(),
            self.view._orientacion_values.get(self.view._combo_orientacion.get()))

    def form_values(self):
        """Lee valores actuales y traduce opciones visibles a sus valores EXIF."""
        return {key: self.view._enum_values[key].get(widget.get(), '') if key in self.view._enum_values
                else widget.get().strip() for key, widget in self.view._campos_edit.items()}

    def activate(self, key, *, force=False, preserve_notice=False):
        """Selecciona un archivo y solicita su lectura para la revisión actual."""
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
        """Aplica datos y preview solo si selección y revisión siguen vigentes."""
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
            if item.status in ('meta_pending', 'meta_read_error', 'meta_ready', 'meta_no_exif', 'meta_format_unsupported', 'unsupported_frames'):
                item.status = ('meta_format_unsupported' if not data.get('supported', True) else
                               'unsupported_frames' if not data.get('writable', True) else
                               'meta_read_error' if data['edit_error'] and not data['metadata'] else
                               'meta_ready' if data['metadata'] else 'meta_no_exif')
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
                self.view._info_tecnica.configure(text=error_text(data.get('blocked_reason') or 'meta_read_only') if not data['edit_error'] else error_text(data['edit_error']))
            self.view._aplicar_metadatos(data['metadata'])
            self.view._lbl_info.configure(text=self.notice or (
                self.feedback if self.tab != t('clean_batch') else ''))
        self.render_previews()
        self.refresh()

    def set_form(self, values, *, enabled):
        """Carga al formulario los valores del archivo activo sin perder borradores."""
        for widget in self.view._campos_edit.values():
            configure_changed(widget, state='readonly' if isinstance(widget, ctk.CTkComboBox) else 'normal')
        self.view._aplicar_campos_edit(values)
        for widget in [*self.view._campos_edit.values(), self.view._combo_orientacion,
                       self.view._sync_dates_check, self.view._clear_gps_check]:
            configure_changed(widget, state=('readonly' if isinstance(widget, ctk.CTkComboBox) else 'normal') if enabled else 'disabled')

    def render_previews(self, placeholder=''):
        """Actualiza las previsualizaciones vinculadas a la pestaña visible."""
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
        """Cambia de pestaña conservando el borrador del archivo activo."""
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
        """Expande o contrae los detalles EXIF del archivo seleccionado."""
        self.details_expanded = not self.details_expanded
        self.view._sync_presentation()

    def _dialog(self, title, width, height):
        """Construye un diálogo local ligado a la ventana del módulo."""
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
        center_on_parent(dialog, self.view, modal=True)
        return dialog

    @staticmethod
    def _dialog_icon(dialog):
        """Carga el icono del diálogo desde los recursos de la app."""
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
        """Crea una acción del diálogo con el estilo de Yagua."""
        return styles.Button(parent, role='primary' if primary else 'secondary',
            text=t(key), command=command, height=40, width=1, font=fonts.FUENTE_BASE)

    def destination(self, count_items, *, choose_scope=False) -> 'Any':
        """Choose the save scope; this dialog also confirms overwriting originals."""
        from app.ui.saving import mode
        overwrite = mode(self.view) == 'overwrite'
        if not choose_scope:
            folder = None if overwrite else filedialog.askdirectory(parent=self.view, title=t('select_output_folder_clean'))
            return (overwrite, folder) if overwrite or folder else None
        dialog = self._dialog('meta_save', 540, 320)
        dialog.minsize(440, 320)
        current = self.state.current
        current_editable = bool(current and current.data and current.data['editable'] and not current.data['edit_error'])
        ctk.CTkLabel(dialog, text=t('meta_save_scope'), font=fonts.FUENTE_BASE, anchor='w',
            justify='left', wraplength=480).grid(row=0, column=0, padx=20, pady=(16, 8), sticky='ew')
        explanation = t('meta_save_overwrite_notice' if overwrite else 'meta_save_copies_notice')
        ctk.CTkLabel(dialog, text=explanation, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            anchor='w', justify='left', wraplength=480).grid(row=1, column=0, padx=20, pady=(0, 8), sticky='ew')
        ctk.CTkLabel(dialog, text=t('meta_save_nonempty'), font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w', justify='left', wraplength=480).grid(
                row=2, column=0, padx=20, pady=(0, 12), sticky='ew')
        result = []
        def accept(selected):
            """Only choose a folder after the scope; cancelling preserves all drafts."""
            folder = None if overwrite else filedialog.askdirectory(parent=dialog, title=t('select_output_folder_clean'))
            if not overwrite and not folder:
                return
            result.append((selected, overwrite, folder))
            dialog.destroy()
        current_button = self._dialog_button(dialog, 'meta_save_current_action', lambda: accept(False))
        current_button.grid(row=3, column=0, padx=20, pady=(0, 8), sticky='ew')
        current_button.configure(state='normal' if current_editable else 'disabled')
        count = len(self.state.marked)
        batch_button = self._dialog_button(dialog, 'meta_save_marked_action', lambda: accept(True), primary=True)
        batch_button.configure(text=t('meta_save_marked_action').format(count=count),
            state='normal' if count and any(self.compatible(item) for item in self.state.marked) else 'disabled')
        batch_button.grid(row=4, column=0, padx=20, pady=(0, 8), sticky='ew')
        self._dialog_button(dialog, 'meta_cancel', dialog.destroy).grid(
            row=5, column=0, padx=20, pady=(0, 16), sticky='ew')
        self.view.wait_window(dialog)
        return result[0] if result else None

    def save(self, *, selected: bool | None = False, clean=False):
        """Apply the open form to the chosen scope and save immutable per-file tasks."""
        if self.view._operation_blocked(global_job=True):
            return
        self.capture()
        current = self.state.current
        source = MetadataDraft()
        if not clean and current and current.data and current.data['editable'] and not current.data['edit_error']:
            source = MetadataDraft({key: value for key, value in self.form_values().items() if value},
                current.draft.sync_dates, current.draft.clear_gps, current.draft.orientation)
            _, error = preparar_borrador(current.data['values'], source)
            if error and error != 'empty':
                self.view._lbl_info.configure(text=error_text(error))
                return
        if not clean and not source.dirty and not any(item.draft.dirty for item in self.state.items.values()):
            self.view._lbl_info.configure(text=t('no_metadata_changes'))
            return
        destination = None
        if selected is None:
            if not current and not self.state.marked:
                self.view._lbl_info.configure(text=t('meta_no_selection'))
                return
            chosen = self.destination(len(self.state.marked), choose_scope=True)
            if chosen is None:
                return
            selected, overwrite, folder = chosen
            destination = (overwrite, folder)
        items = self.state.marked if selected else ([current] if current else [])
        if not items:
            self.view._lbl_info.configure(text=t('meta_no_selection'))
            return
        if not clean and not selected and (not current or not current.data or not current.data['editable'] or current.data['edit_error']):
            self.view._lbl_info.configure(text=t('meta_read_only'))
            return
        tasks = tuple(MetadataTask(item.path,
                                   combinar_formulario(item.draft, source) if selected and not clean else item.draft.copy(),
                                   item.data['fingerprint'] if item.data else None) for item in items)
        if destination is None:
            destination = self.destination(len(tasks))
        if destination is None:
            return
        overwrite, folder = destination
        def start(_folder, plan=None):
            """The scope choice confirms edits; cleanup keeps its separate warning."""
            if not clean and selected:
                for task in tasks:
                    item = self.state.items.get(path_key(task.path))
                    if item and self.compatible(item):
                        item.draft = task.draft.copy()
            self.epoch += 1
            self._thumb_requests.clear()
            self.revision += 1
            self.view._lbl_info.configure(text=t('processing'))
            def work():
                """Plan and save outside Tk after the user confirms the scope."""
                with self.io_lock:
                    output = plan if plan is not None else plan_outputs(
                        tuple(task.path for task in tasks), _folder, 'overwrite' if overwrite else 'copies')
                    return procesar_lote(tasks, clean=clean, overwrite=overwrite,
                                         folder=_folder, output_policy=output)
            self.view._submit_job(work, on_success=lambda result: self.finished(result, overwrite))
        if clean:
            self.view._prepare_save(tuple(task.path for task in tasks), None, start, folder=folder,
                                    notice=t('meta_clean_confirm'))
        else:
            start(folder)

    def finished(self, result, overwrite):
        """Libera estado de operación y presenta resultados parciales del lote."""
        lines = []
        for row in result['items']:
            item = self.state.items.get(path_key(row['ruta']))
            if item is None:
                continue
            status = row['estado']
            item.status = {'saved': 'meta_saved' if overwrite else 'meta_copied',
                           'unchanged': 'no_metadata_changes', 'unsupported': 'meta_format_unsupported',
                           'skipped': row.get('motivo', 'meta_format_unsupported'), 'error': 'error_generic'}[status]
            item.detail = row['destino'] if status == 'saved' else error_text(row['error'])
            lines.append(f'{item.path}\n{t(item.status)}: {item.detail}')
            if status == 'saved' and overwrite:
                image_cache.invalidate(item.path)
                item.data = None
                item.draft = MetadataDraft()
                item.thumbnail = None
                self.enqueue('thumb', path_key(item.path))
        self.summary = operation_summary(result['ok'], result['errores'], unchanged=result['unchanged'],
                                         skipped=result.get('omitidos', 0))
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

    def export(self, fmt):
        """Exporta los metadatos seleccionados al formato pedido."""
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
            """Lee o exporta las rutas capturadas fuera del hilo de interfaz."""
            with self.io_lock:
                if batch:
                    return exportar_lote(paths, destination, fmt)
                data = leer_archivo(paths[0])
                if not data['supported']:
                    raise ValueError('meta_format_unsupported')
                if data.get('read_error'):
                    raise ValueError('meta_read_error')
                from app.modules.metadata import exportar_metadatos
                exportar_metadatos(data['metadata'], destination, fmt)
                return []
        def success(entries):
            """Marca fallos individuales y anuncia la ruta del archivo exportado."""
            for entry in entries:
                item = self.state.items.get(path_key(entry['ruta']))
                if item and entry['error']:
                    item.status, item.detail = ('meta_format_unsupported' if entry['error'] == 'meta_format_unsupported' else 'meta_read_error'), error_text(entry['error'])
            self.refresh()
            self.view._lbl_info.configure(text=f'{t("exported_as")} {Path(destination).name}')
        self.view._submit_job(work, on_success=success,
            on_error=lambda error: self.view._lbl_info.configure(text=f'{t("error_saving")}: {error}'))

    def clear(self):
        """Limpia los campos EXIF seleccionados de una copia segura."""
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
