"""Batch palette workspace with reusable rows, swatches and lazy extraction."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock, Thread
from tkinter import filedialog

import customtkinter as ctk

from app.modules.palette_batch import PaletteCache, process_palettes
from app.ui import colors, fonts, styles
from app.ui.building import stepwise
from app.ui.file_list import FileList
from app.ui.operations import operations
from app.ui.rendering import configure_changed
from app.ui.status import operation_summary
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.palette.services import exportar_paleta_imagen, formatos_color, rgb_a_hex
from app.ui.frames.palette.state import PaletteState

logger = logging.getLogger(__name__)


class PaletteFrame(BaseFrame):
    """Inspect one palette while extracting or exporting a bounded collection."""

    design_system = True

    def __init__(self, parent, *, defer_build=False):
        """Inicializa colección, caché y revisión de solicitudes antes de construir Tk."""
        self._state = PaletteState()
        self._cache = PaletteCache()
        self._request_lock = Lock()
        self._pending = None
        self._worker_running = False
        self._closed = False
        self._revision = 0
        self._copy_timer = None
        self._results = []
        self._visible_color_count = 0
        super().__init__(parent, t('palette_title'), defer_build=defer_build)

    def _on_build_complete(self):
        """Activa únicamente las acciones que ya tienen imágenes o resultados."""
        super()._on_build_complete()
        self._update_controls()

    @stepwise
    def _build_content(self):
        """Create controls once, preserving incremental startup construction."""
        self._btn_seleccionar = self._crear_boton_seleccionar(
            self, t('palette_add_images'), self._explorar)
        self._btn_seleccionar.grid(row=1, column=0, padx=24, pady=(8, 12), sticky='ew')
        yield
        self._frame_preview = ctk.CTkFrame(self, height=160, **styles.surface('list'))
        self._frame_preview.grid(row=3, column=0, padx=24, pady=(0, 12), sticky='ew')
        self._frame_preview.grid_propagate(False)
        self._frame_preview.grid_columnconfigure(0, weight=1)
        self._frame_preview.grid_rowconfigure(1, weight=1)
        yield
        self._count_label = ctk.CTkLabel(self._frame_preview, text='', font=fonts.FUENTE_CHICA,
                                        text_color=colors.TEXT_GRAY, anchor='w')
        self._count_label.grid(row=0, column=0, sticky='ew', padx=12, pady=(4, 0))
        yield
        self._lista_frame = ctk.CTkScrollableFrame(self._frame_preview, height=120,
            corner_radius=0, fg_color=styles.palette().inset, **styles.scrollbar())
        self._lista_frame.grid(row=1, column=0, sticky='nsew', padx=1, pady=1)
        self._lista_frame._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        yield
        self._files = FileList(self._lista_frame, self._filas_lista, self._thumbs,
                               design_system=True, on_select=self._select_image)
        self._files.sync([])
        yield
        self._panel_paleta = ctk.CTkFrame(self, **styles.surface('panel'))
        self._panel_paleta.grid(row=2, column=0, padx=24, pady=(0, 8), sticky='ew')
        self._panel_paleta.grid_columnconfigure(0, weight=1)
        yield
        top = ctk.CTkFrame(self._panel_paleta, fg_color='transparent', corner_radius=0)
        top.grid(row=0, column=0, padx=16, pady=(8, 8), sticky='ew')
        top.grid_columnconfigure(0, weight=1)
        yield
        self._active_label = ctk.CTkLabel(top, text=t('colors_to_extract'), width=1,
            anchor='w', font=fonts.FUENTE_BASE, text_color=colors.TEXT_GRAY)
        self._active_label.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        yield
        self._seg_n = styles.SegmentedButton(top, values=['4', '6', '8', '10', '12'],
            font=fonts.FUENTE_CHICA, command=self._auto_extraer)
        self._seg_n.set('6')
        self._seg_n.grid(row=0, column=1, sticky='e')
        yield
        self._swatch_host = ctk.CTkFrame(self._panel_paleta, height=240, **styles.surface('list'))
        self._swatch_host.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')
        self._swatch_host.grid_propagate(False)
        self._swatch_host.grid_columnconfigure(0, weight=1)
        self._swatch_host.grid_rowconfigure(0, weight=1)
        yield
        self._swatches_frame = ctk.CTkScrollableFrame(self._swatch_host, height=222,
            orientation='horizontal', corner_radius=0, fg_color=styles.palette().inset,
            **styles.scrollbar())
        self._swatches_frame.grid(row=0, column=0, sticky='nsew', padx=1, pady=1)
        self._swatches_frame._scrollbar.configure(corner_radius=0, height=6, border_spacing=1)
        self._swatches_frame._parent_canvas.bind('<Configure>', self._fit_swatches_width, add=True)
        self._swatch_pool = []
        yield
        self._palette_empty = ctk.CTkLabel(self._swatch_host, text=t('load_image_for_palette'),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY)
        self._palette_empty.place(relx=.5, rely=.5, anchor='center')
        yield
        self._actions = actions = ctk.CTkFrame(self, fg_color='transparent', corner_radius=0)
        actions.grid(row=4, column=0, padx=24, pady=(0, 12), sticky='ew')
        actions.grid_columnconfigure((0, 1), weight=1, uniform='actions')
        yield
        self._btn_guardar = self._new_button(actions, text=t('palette_save_open'),
            font=fonts.FUENTE_BASE, command=self._guardar_imagen)
        self._btn_guardar.grid(row=0, column=0, sticky='ew', padx=(0, 4))
        yield
        self._btn_guardar_todas = self._new_button(actions, role='primary', text=t('palette_save_all'),
            font=fonts.FUENTE_BASE, command=self._guardar_todas)
        self._btn_guardar_todas.grid(row=0, column=1, sticky='ew', padx=(4, 0))
        yield

    def _update_controls(self):
        """Enable only actions that have an input or a current palette."""
        self._btn_guardar.configure(state='normal' if self._state.paleta else 'disabled')
        self._btn_guardar_todas.configure(state='normal' if self._state.paths else 'disabled')
        self._count_label.configure(text=t('palette_image_count').format(count=len(self._state.paths))
                                    if self._state.paths else '')

    def _empty_palette(self, message):
        """Hide obsolete colors without destroying reusable swatches."""
        self._state.paleta = []
        self._visible_color_count = 0
        for col, *_rest in self._swatch_pool:
            col.grid_remove()
        self._palette_empty.configure(text=message)
        self._palette_empty.place(relx=.5, rely=.5, anchor='center')

    def _fit_swatches_width(self, _event=None):
        """Fill the viewport, keeping horizontal scrolling only when needed."""
        canvas = self._swatches_frame._parent_canvas
        width = max(canvas.winfo_width(), self._visible_color_count * 72)
        window = self._swatches_frame._create_window_id
        if int(float(canvas.itemcget(window, 'width'))) != width:
            canvas.itemconfigure(window, width=width)

    def _renderizar_paleta(self, paleta: list[tuple[int, int, int]]):
        """Renderizar los swatches de color en el panel.

        Args:
            paleta: Lista de tuplas RGB con los colores extraidos
        """
        self._palette_empty.place_forget()
        self._visible_color_count = len(paleta)
        for index, (col, canvas, label, buttons) in enumerate(self._swatch_pool):
            if index >= len(paleta):
                col.grid_remove()
            self._swatches_frame.grid_columnconfigure(index, weight=0, minsize=0, uniform='')
        for indice, color_rgb in enumerate(paleta):
            hex_color = rgb_a_hex(color_rgb)
            if indice == len(self._swatch_pool):
                col = ctk.CTkFrame(self._swatches_frame, corner_radius=0, fg_color='transparent')
                col.grid_columnconfigure(0, weight=1)
                # Use a scaled CTk swatch: a native 50px canvas kept its full
                # height at 50% scale and clipped the last copy button.
                canvas = ctk.CTkFrame(col, width=50, height=64, corner_radius=0,
                                      border_width=0, fg_color=hex_color, cursor='hand2')
                canvas.grid(row=0, column=0, sticky='ew')
                label = ctk.CTkLabel(col, text='', font=ctk.CTkFont(size=9), text_color=colors.TEXT_GRAY)
                label.grid(row=1, column=0, pady=(3, 2))
                buttons = []
                for row, formato in enumerate(formatos_color(color_rgb), 2):
                    button = self._new_button(col, role='secondary', text=formato, width=50, height=28,
                        font=ctk.CTkFont(size=9))
                    button.grid(row=row, column=0, pady=1, sticky='ew')
                    buttons.append(button)
                self._swatch_pool.append((col, canvas, label, buttons))
            col, canvas, label, buttons = self._swatch_pool[indice]
            if getattr(col, '_rgb', None) != color_rgb:
                col._rgb = color_rgb
                canvas.configure(fg_color=hex_color)
                configure_changed(label, text=hex_color)
                for button, valor in zip(buttons, formatos_color(color_rgb).values()):
                    button.configure(command=lambda v=valor: self._copiar(v))
            self._swatches_frame.grid_columnconfigure(indice, weight=1, uniform='swatch', minsize=68)
            col.grid(row=0, column=indice, padx=2, pady=(4, 8), sticky='nsew')
        self.after_idle(self._fit_swatches_width)

    def _copiar(self, valor):
        """Copy a color without letting a previous notification replace new state."""
        self.clipboard_clear()
        self.clipboard_append(valor)
        self._lbl_info.configure(text=f'{t("copied")} {valor}')
        if self._copy_timer is not None:
            self.after_cancel(self._copy_timer)
        revision = self._revision
        def restore():
            self._copy_timer = None
            if revision == self._revision:
                self._lbl_info.configure(text='')
        self._copy_timer = self.after(2000, restore)

    def _explorar(self):
        """Añade una selección múltiple sin interrumpir operaciones de guardado."""
        if self._operation_blocked(global_job=True):
            return
        paths = filedialog.askopenfilenames(title=t('palette_add_images'),
            filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.avif *.heic *.heif *.gif *.ico')])
        if paths:
            self._add_images(paths)

    def _add_images(self, paths):
        """Keep selection and rows while appending a bounded, deduplicated load."""
        duplicates, excluded = self._state.add(paths)
        self._imagenes = list(self._state.paths)
        self._files.sync(self._state.paths)
        self._update_controls()
        notices = []
        if excluded:
            notices.append(t('palette_excluded').format(count=excluded))
        elif len(self._state.paths) == 100:
            notices.append(t('palette_limit'))
        if duplicates:
            notices.append(t('palette_duplicates').format(count=duplicates))
        self._lbl_info.configure(text=' · '.join(notices))

    def _select_image(self, path):
        """Abre una fila e invalida colores y respuestas de la selección anterior."""
        if operations.is_busy(self):
            return False
        self._state.ruta = path or None
        self._revision += 1
        if not path:
            return True
        self._active_label.configure(text=Path(path).name)
        self._empty_palette(t('processing'))
        self._lbl_info.configure(text='')
        self._update_controls()
        self._queue_extract(path, int(self._seg_n.get()))
        return True

    def _auto_extraer(self, *_):
        """Recalcula sólo la imagen abierta con la nueva cantidad de colores."""
        if self._operation_blocked(global_job=True) or not self._state.ruta:
            return
        self._select_image(self._state.ruta)

    def _queue_extract(self, path, count):
        """One running extraction and only the most recent pending request."""
        request = self._revision, path, count, self._cache
        with self._request_lock:
            self._pending = request
            if self._worker_running:
                return
            self._worker_running = True
        try:
            Thread(target=self._extract_worker, daemon=True).start()
        except Exception:
            with self._request_lock:
                self._worker_running = False
                self._pending = None
            self._deliver_palette(request, (), 'palette_read_error')

    def _extract_worker(self):
        """Read and quantize outside Tk, replacing obsolete pending requests."""
        while True:
            with self._request_lock:
                request, self._pending = self._pending, None
                if request is None or self._closed:
                    self._worker_running = False
                    return
            revision, path, count, cache = request
            try:
                palette, error = cache.extract(path, count), ''
            except Exception as exc:
                logger.warning('palette extraction failed: %s: %s', path, exc)
                palette, error = (), str(exc)
            operations.post(self, lambda req=request, colors=palette, err=error:
                            self._deliver_palette(req, colors, err))

    def _deliver_palette(self, request, palette, error):
        """Aplica una respuesta vigente en Tk y mantiene los errores por archivo."""
        if request[0] != self._revision or self._closed:
            return
        if error:
            message = t('palette_no_visible_colors' if error == 'palette_no_visible_colors'
                        else 'palette_read_error')
            self._empty_palette(message)
            self._set_file_error(self._state.ruta, message)
        else:
            self._set_file_error(self._state.ruta, '')
            self._aplicar_paleta(list(palette))
        self._update_controls()

    def _set_file_error(self, path, message):
        """Update an error on its visible row without rebuilding or decoding it."""
        self._files.statuses[path] = message
        for key, row in self._files.virtual.rows.items():
            if key[0] == path:
                base = row.info_label.cget('text').split(' · ')[0]
                configure_changed(row.info_label, text=base + (f' · {message}' if message else ''))

    def _aplicar_paleta(self, paleta):
        self._state.paleta = paleta
        self._renderizar_paleta(paleta)
        self._update_controls()

    def _batch(self, folder=None):
        """Captura el lote y procesa en serie con progreso y resultados separados."""
        if self._operation_blocked(global_job=True) or not self._state.paths:
            return
        self._revision += 1
        with self._request_lock:
            self._pending = None
        paths, count, cache = tuple(self._state.paths), int(self._seg_n.get()), self._cache
        revision = self._revision
        self._show_full_overlay(t('processing'))
        assert self._full_overlay_bar is not None
        bar = self._full_overlay_bar
        bar.stop()
        bar.configure(mode='determinate')
        bar.set(0)
        def progress(done, total):
            operations.post(self, lambda: self._progress(revision, done, total))
        def work():
            return process_palettes(paths, count, cache, folder=folder, progress=progress)
        def finished(results):
            bar.configure(mode='indeterminate')
            self._results = results
            for item in results:
                if item['path'] == self._state.ruta:
                    self._deliver_palette((revision,), item['palette'], item['error'])
                if item['error']:
                    logger.warning('palette batch failed: %s: %s', item['path'], item['error'])
                self._set_file_error(item['path'], t('palette_no_visible_colors')
                    if item['error'] == 'palette_no_visible_colors'
                    else t('palette_read_error') if item['error'] else '')
            errors = sum(bool(item['error']) for item in results)
            self._lbl_info.configure(text=operation_summary(len(results) - errors, errors,
                                    action='saved' if folder is not None else 'processed'))
            self._update_controls()
        self._submit_job(work, on_success=finished)

    def _progress(self, revision, done, total):
        """Actualiza el avance sólo mientras sigue activa esta operación."""
        if (revision == self._revision and operations.is_busy(self)
                and self._full_overlay_label is not None and self._full_overlay_bar is not None):
            self._full_overlay_label.configure(text=f'{t("processing")} {done}/{total}')
            self._full_overlay_bar.set(done / total)

    def _guardar_todas(self):
        """Pide una carpeta; cancelar conserva la colección y no escribe archivos."""
        if self._operation_blocked(global_job=True) or not self._state.paths:
            return
        folder = filedialog.askdirectory(title=t('palette_save_all'))
        if folder:
            self._batch(folder)

    def _guardar_imagen(self):
        """Exporta la paleta abierta, releyendo cambios y protegiendo el lote."""
        if self._operation_blocked(global_job=True) or not self._state.paleta:
            return
        source, count, cache = self._state.ruta, int(self._seg_n.get()), self._cache
        if source is None:
            return
        path = filedialog.asksaveasfilename(title=t('save_palette'), defaultextension='.png',
            filetypes=[('PNG', '*.png')], initialfile=f'{Path(source).stem}_paleta.png')
        if not path:
            return
        from app.modules.palette_batch import path_key
        if path_key(path) in self._state.paths:
            self._lbl_info.configure(text=t('palette_source_protected'))
            return
        self._show_full_overlay(t('processing'))
        def work():
            # Revalidate the source even if the palette was shown earlier.
            palette = cache.extract(source, count)
            exportar_paleta_imagen(palette, path)
            return palette
        def finished(palette):
            self._aplicar_paleta(list(palette))
            self._lbl_info.configure(text=operation_summary(1))
        self._submit_job(work, on_success=finished)

    def _limpiar(self):
        """Vacía datos y caché sin destruir filas ni aceptar respuestas antiguas."""
        if self._operation_blocked(global_job=False):
            return
        self._revision += 1
        with self._request_lock:
            self._pending = None
        self._cache = PaletteCache()
        self._state = PaletteState()
        self._imagenes = []
        self._results = []
        self._files.statuses.clear()
        self._files.sync([])
        self._empty_palette(t('load_image_for_palette'))
        self._active_label.configure(text=t('colors_to_extract'))
        self._lbl_info.configure(text='')
        self._update_controls()

    def destroy(self):
        """Stop pending work; late deliveries are ignored by the coordinator."""
        with self._request_lock:
            self._closed = True
            self._pending = None
        super().destroy()
