"""Small collection and preview widgets, shared by the three metadata tabs."""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.modules.compress import formatear_bytes
from app.translations import t
from app.ui import colors, fonts
from app.ui.lifetime import UiLifetime
from app.ui.rendering import StableRender, VirtualRows, PooledRow, configure_changed
from app.ui.frames.metadata.state import MetadataState


class MetadataFiles(ctk.CTkFrame):
    tab_frame: object = None
    def __init__(self, parent, state: MetadataState, activate, mark, mark_all):
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
        buttons.grid(row=1, column=0, sticky='ew', pady=(4, 6))
        buttons.grid_columnconfigure((0, 1), weight=1)
        for column, (text, value) in enumerate((('meta_mark_all', True), ('meta_unmark_all', False))):
            ctk.CTkButton(buttons, text=t(text), width=1, height=28,
                          fg_color=colors.SIDEBAR_BG, hover_color=colors.SIDEBAR_HOVER,
                          text_color=colors.TEXT_COLOR, font=fonts.FUENTE_CHICA,
                          command=lambda v=value: mark_all(v)).grid(row=0, column=column, padx=2, sticky='ew')
        # The CTk scrollbar otherwise imposes its own 200px requested height.
        viewport = ctk.CTkFrame(self, height=136, fg_color='transparent')
        viewport.grid(row=2, column=0, sticky='ew')
        viewport.grid_propagate(False)
        viewport.grid_columnconfigure(0, weight=1)
        viewport.grid_rowconfigure(0, weight=1)
        self.list = ctk.CTkScrollableFrame(viewport, height=136, corner_radius=0, fg_color='transparent', border_width=0)
        self.list.grid(row=0, column=0, sticky='nsew')
        self.list.grid_columnconfigure(0, weight=1)
        self.empty = ctk.CTkLabel(self.list, text=t('no_images'), text_color=colors.TEXT_GRAY)
        self.virtual = VirtualRows(self.list, self._create_row, self._render_row, row_height=72)
        self.refresh()

    @property
    def rows(self):
        return {key: (row, row.variable, row.thumb, row.info_label, row.status_label)
                for key, row in self.virtual.rows.items()}

    def rebuild(self):
        self.refresh()

    def _create_row(self, parent):
        row = PooledRow(parent, fg_color=colors.DROPZONE_BG, border_width=1, corner_radius=8)
        row.grid_columnconfigure(2, weight=1)
        row.variable = ctk.BooleanVar(value=False)
        box = ctk.CTkCheckBox(row, text='', width=24, checkbox_width=18, checkbox_height=18,
            fg_color=colors.ACENTO, hover_color=colors.ACENTO_HOVER,
            checkmark_color=colors.TEXT_ACTIVE, border_color=colors.DROPZONE_BORDER,
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
            if row.key:
                self.activate(row.key)
        row.bind('<Button-1>', activate, add=True)
        for widget in (row.thumb, row.name_label, row.info_label, row.status_label):
            widget.bind('<Button-1>', activate, add='+')
            widget.configure(cursor='hand2')
        return row

    def _render_row(self, row, key):
        item = self.state.items.get(key)
        if item is None:
            return
        if row.variable.get() != item.checked:
            row.variable.set(item.checked)
        configure_changed(row, border_color=colors.ACENTO if key == self.state.active else colors.SIDEBAR_SEPARATOR)
        name = Path(item.path).name
        configure_changed(row.name_label, text=name if len(name) <= 32 else name[:29] + '…')
        configure_changed(row.info_label, text=f'{item.format or Path(item.path).suffix[1:].upper()} · {formatear_bytes(item.size_bytes)}')
        status = t(item.status) + (' · ' + t('meta_draft') if item.draft.dirty else '')
        if item.detail:
            status += ' · ' + item.detail
        configure_changed(row.status_label, text=status)
        if row.thumb.cget('image') is not item.thumbnail:
            row.thumb.configure(image=item.thumbnail)
            if item.thumbnail is None:
                row.thumb._label.configure(image='')
        if item.thumbnail is None:
            self.request_thumbnail(key)

    def refresh(self, key=None):
        text = t('meta_collection_count').format(count=len(self.state.items), marked=len(self.state.marked))
        added, excluded, duplicates = self.state.last_addition
        if excluded or duplicates:
            text += '\n' + t('meta_added').format(added=added, excluded=excluded, duplicates=duplicates)
        configure_changed(self.count, text=text)
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
    tab_frame: object = None
    def __init__(self, parent, *, height=240):
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
                                     fg_color='transparent', corner_radius=8)
        self.viewport.grid(row=1, column=0, sticky='nsew')
        self.viewport.grid_propagate(False)
        self.image = ctk.CTkLabel(self.viewport, text=t('select_image_view'), width=1, height=1,
                                 fg_color=colors.DROPZONE_BG, corner_radius=8,
                                 text_color=colors.TEXT_GRAY, justify='center')
        # place ignores the image's requested size when allocating its viewport.
        self.image.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.renderer = StableRender(self, self.viewport, self.render)
        self.info = ctk.CTkLabel(self, text='', width=1, anchor='w', justify='left', font=fonts.FUENTE_CHICA,
                                text_color=colors.TEXT_GRAY)
        self.info.grid(row=2, column=0, sticky='ew', pady=(6, 0))
        self.viewport.bind('<Configure>', self._wrap, add=True)

    def _wrap(self, event):
        width = max(1, int(event.width / self._get_widget_scaling()) - 24)
        for label in (self.name, self.info, self.image):
            configure_changed(label, wraplength=width)

    def show(self, path='', source=None, info='', error=''):
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
        self.renderer.request()

    def set_visible(self, visible):
        self.renderer.set_visible(visible)

    def render(self, measurements):
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
