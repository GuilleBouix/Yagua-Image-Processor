"""Widgets compactos para la lista y vista previa de las pestañas EXIF."""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.modules.compress import formatear_bytes
from app.translations import t
from app.ui import colors, fonts, styles
from app.ui.lifetime import UiLifetime
from app.ui.rendering import StableRender, VirtualRows, PooledRow, configure_changed
from app.ui.frames.metadata.state import MetadataState


class MetadataFiles(ctk.CTkFrame):
    """Lista virtualizada de archivos con selección y acciones por imagen."""
    tab_frame: object = None
    def __init__(self, parent, state: MetadataState, activate, mark, mark_all):
        """Conecta la lista con el estado y las acciones del módulo."""
        super().__init__(parent, fg_color='transparent')
        self.state = state
        self.activate, self.mark = activate, mark
        self.active_view = False
        self.request_thumbnail = lambda key: None
        self.grid_columnconfigure(0, weight=1)
        self.count = ctk.CTkLabel(self, text='', anchor='w', justify='left', width=1, height=18, font=fonts.FUENTE_CHICA)
        self.count.grid(row=0, column=0, sticky='ew')
        self.bind('<Configure>', lambda event: self.count.configure(
            wraplength=max(100, int(event.width / self._get_widget_scaling()) - 8)), add=True)
        buttons = ctk.CTkFrame(self, fg_color='transparent')
        self.buttons = buttons
        buttons.grid(row=1, column=0, sticky='ew', pady=(4, 6))
        buttons.grid_columnconfigure((0, 1), weight=1)
        for column, (text, value) in enumerate((('meta_mark_all', True), ('meta_unmark_all', False))):
            styles.Button(buttons, text=t(text), width=1, height=30,
                          font=fonts.FUENTE_CHICA,
                          command=lambda v=value: mark_all(v)).grid(row=0, column=column, padx=2, sticky='ew')
        # La barra de CTk impondría de otro modo su altura solicitada de 200 px.
        viewport = ctk.CTkFrame(self, height=136, fg_color='transparent')
        viewport.grid(row=2, column=0, sticky='ew')
        viewport.grid_propagate(False)
        viewport.grid_columnconfigure(0, weight=1)
        viewport.grid_rowconfigure(0, weight=1)
        self.list = ctk.CTkScrollableFrame(viewport, height=136,
            **styles.surface('list'), **styles.scrollbar())
        self.list._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        self.list.grid(row=0, column=0, sticky='nsew')
        self.list.grid_columnconfigure(0, weight=1)
        self.empty = ctk.CTkLabel(self.list, text=t('meta_start'), text_color=colors.TEXT_GRAY,
                                  font=fonts.FUENTE_CHICA, wraplength=240)
        self.virtual = VirtualRows(self.list, self._create_row, self._render_row, row_height=72)
        self.refresh()

    @property
    def rows(self):
        """Devuelve las filas que corresponden a la revisión actual."""
        return {key: (row, row.variable, row.thumb, row.info_label, row.status_label)
                for key, row in self.virtual.rows.items()}

    def rebuild(self):
        """Reconstruye solo las filas necesarias para la selección actual."""
        self.refresh()

    def _create_row(self, parent):
        """Crea una fila reutilizable para un archivo de la lista."""
        row = PooledRow(parent, **styles.surface('row'))
        row.grid_columnconfigure(2, weight=1)
        row.variable = ctk.BooleanVar(value=False)
        box = styles.CheckBox(row, text='', width=24, checkbox_width=18, checkbox_height=18,
            variable=row.variable, command=lambda: self.mark(row.key, row.variable.get()) if row.key else None)
        box.grid(row=0, column=0, rowspan=3, padx=(6, 2))
        row.thumb = ctk.CTkLabel(row, text='', width=44, height=44)
        row.thumb.grid(row=0, column=1, rowspan=3, padx=(2, 6), pady=6)
        row.name_label = ctk.CTkLabel(row, text='', anchor='w', font=fonts.FUENTE_BASE, height=18, width=1)
        row.name_label.grid(row=0, column=2, padx=(0, 6), pady=(6, 0), sticky='ew')
        row.info_label = ctk.CTkLabel(row, text='', font=fonts.FUENTE_CHICA, anchor='w', height=16,
                               text_color=colors.TEXT_GRAY, width=1)
        row.info_label.grid(row=1, column=2, sticky='ew', padx=(0, 6))
        row.status_label = ctk.CTkLabel(row, text='', font=fonts.FUENTE_CHICA, anchor='w', height=16,
                                 text_color=colors.TEXT_GRAY, width=1)
        row.status_label.grid(row=2, column=2, padx=(0, 6), pady=(0, 6), sticky='ew')
        def activate(_event):
            """Activa la fila al pulsar cualquiera de sus controles visuales."""
            if row.key:
                self.activate(row.key)
        row.bind('<Button-1>', activate, add=True)
        for widget in (row.thumb, row.name_label, row.info_label, row.status_label):
            widget.bind('<Button-1>', activate, add='+')
            widget.configure(cursor='hand2')
        return row

    def _render_row(self, row, key):
        """Actualiza una fila con ruta, selección y estado del archivo."""
        item = self.state.items.get(key)
        if item is None:
            return
        if row.variable.get() != item.checked:
            row.variable.set(item.checked)
        p = styles.palette()
        configure_changed(row, border_color=p.primary if key == self.state.active else p.border)
        name = Path(item.path).name
        configure_changed(row.name_label, text=name if len(name) <= 32 else name[:29] + '…')
        configure_changed(row.info_label, text=f'{item.format or Path(item.path).suffix[1:].upper()} · {formatear_bytes(item.size_bytes)}')
        status = '' if item.status in ('meta_pending', 'meta_ready', 'meta_no_exif') else t(item.status)
        if item.draft.dirty:
            status += (' · ' if status else '') + t('meta_draft')
        if item.detail and item.status == 'meta_read_error':
            status += ' · ' + item.detail
        configure_changed(row.status_label, text=status)
        if row.thumb.cget('image') is not item.thumbnail:
            row.thumb.configure(image=item.thumbnail)
            if item.thumbnail is None:
                row.thumb._label.configure(image='')
        if item.thumbnail is None:
            self.request_thumbnail(key)

    def refresh(self, key=None):
        """Refresca filas afectadas sin reiniciar toda la lista."""
        count, marked = len(self.state.items), len(self.state.marked)
        text = t('meta_image_count' if count == 1 else 'meta_images_count').format(count=count)
        text += ' · ' + t('meta_selected_one' if marked == 1 else 'meta_selected_count').format(marked=marked)
        configure_changed(self.count, text=text)
        for widget in (self.count, self.buttons):
            if self.state.items and not widget.winfo_manager():
                widget.grid()
            elif not self.state.items and widget.winfo_manager():
                widget.grid_remove()
        if not self.state.items:
            self.virtual.sync(())
        if self.active_view:
            self.virtual.sync(self.state.items)
            if self.state.items:
                self.empty.pack_forget()
            else:
                self.empty.pack(pady=16)
            self.virtual.refresh(key)


class MetadataPreview(UiLifetime, ctk.CTkFrame):
    """Panel de vista previa que ignora cargas antiguas."""
    tab_frame: object = None
    def __init__(self, parent, *, height=240):
        """Inicializa el panel y el estado de su vista previa."""
        super().__init__(parent, fg_color='transparent')
        self.source: Image.Image | None = None
        self.photo: ctk.CTkImage | None = None
        self.size = None
        self.signature = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.name = ctk.CTkLabel(self, text='', width=1, anchor='w', justify='left', font=fonts.FUENTE_BASE)
        self.name.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        self.viewport = ctk.CTkFrame(self, height=height, width=1,
                                     fg_color='transparent', corner_radius=0)
        self.viewport.grid(row=1, column=0, sticky='nsew')
        self.viewport.grid_propagate(False)
        self.image = ctk.CTkLabel(self.viewport, text=t('select_image_view'), width=1, height=1,
                                 fg_color=styles.palette().inset, corner_radius=0,
                                 text_color=colors.TEXT_GRAY, justify='center')
        # place no usa el tamaño solicitado de la imagen para asignar su viewport.
        self.image.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.renderer = StableRender(self, self.viewport, self.render)
        self.info = ctk.CTkLabel(self, text='', width=1, anchor='w', justify='left', font=fonts.FUENTE_CHICA,
                                text_color=colors.TEXT_GRAY)
        self.info.grid(row=2, column=0, sticky='ew', pady=(6, 0))
        self.viewport.bind('<Configure>', self._wrap, add=True)

    def _wrap(self, event):
        """Ajusta el texto de detalles al ancho disponible."""
        width = max(1, int(event.width / self._get_widget_scaling()) - 24)
        for label in (self.name, self.info, self.image):
            configure_changed(label, wraplength=width)

    def show(self, path='', source=None, info='', error=''):
        """Muestra datos de una selección y descarta resultados obsoletos."""
        changed = self.source is not source
        self.source = source
        if changed:
            self.size = None
            self.signature = None
        configure_changed(self.name, text=Path(path).name if path else '')
        configure_changed(self.info, text=info)
        if changed or source is None:
            configure_changed(self.image, image=None,
                              text=error or t('processing' if source is not None else 'select_image_view'))
            if self.photo is not None:
                self.image._label.configure(image='')
                self.photo = None
        self.schedule()

    def schedule(self, _event=None):
        """Agrupa cambios de tamaño antes de volver a dibujar."""
        self.renderer.request()

    def set_visible(self, visible):
        """Pausa la carga de preview si el panel no está visible."""
        self.renderer.set_visible(visible)

    def render(self, measurements):
        """Dibuja la selección vigente en el panel de vista previa."""
        pixels_x, pixels_y, scale = measurements
        width = max(1, int(pixels_x / scale) - 24)
        height = max(1, int(pixels_y / scale) - 24)
        signature = (id(self.source), width, height, scale)
        if self.source is None or self.signature == signature:
            return
        preview = self.source.copy()
        preview.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.photo = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
        self.image.configure(image=self.photo, text='')
        self.size = (width, height)
        self.signature = signature
