"""Pantalla inicial de Yagua, con accesos a los módulos y avisos de arranque."""

from __future__ import annotations

from app.ui.building import finish, stepwise, steps_for
import logging
import webbrowser

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.ui.scale import scale_wraplength
from app.translations import t
from app.utils import tintar_icono
from app.utils.project_links import open_project_page
from app.ui.module_registry import iter_enabled_modules


logger = logging.getLogger(__name__)
GITHUB_REPOSITORY_URL = 'https://github.com/GuilleBouix/Yagua-Image-Processor'


class HomeFrame(ctk.CTkScrollableFrame):
    """Pantalla inicial de bienvenida (solo visual)."""

    def __init__(self, parent, *, defer_build=False):
        """Inicializa el estado visual y los callbacks de la pantalla principal."""
        super().__init__(
            parent,
            fg_color=colors.FRAMES_BG,
            corner_radius=0,
            scrollbar_fg_color=colors.FRAMES_BG,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.SIDEBAR_HOVER,
        )
        logger.info("home.ui: init")
        self._on_select = None
        self._viewport_sync_job = None
        self._build_iterator = steps_for(self._build)
        if not defer_build:
            finish(self._build_iterator)
        self.after(0, self._bind_viewport_sync)

    def set_on_select(self, callback):
        """Conecta las tarjetas de Inicio con la navegación principal."""
        self._on_select = callback

    def on_view_shown(self):
        """Re-sincroniza el viewport al volver a mostrar Home."""
        self._schedule_viewport_sync()

    def on_view_hidden(self):
        """Hook de lifecycle para mantener API consistente con los modulos."""
        return

    def _bind_viewport_sync(self):
        """Mantiene la pantalla Home con al menos el alto del viewport visible."""
        if not hasattr(self, "_parent_canvas"):
            return
        try:
            self._parent_canvas.bind("<Configure>", self._schedule_viewport_sync, add="+")
            self.bind("<Configure>", self._schedule_viewport_sync, add="+")
            self._schedule_viewport_sync()
        except Exception:
            logger.exception("home.ui: no se pudo sincronizar viewport")

    def _schedule_viewport_sync(self, _event=None):
        """Espera al final del ciclo de geometría antes de medir el viewport."""
        if self._viewport_sync_job is not None or not self.winfo_exists():
            return
        try:
            self._viewport_sync_job = self.after_idle(self._sync_viewport_height)
        except Exception:
            logger.debug("home.ui: no se pudo programar sync de viewport", exc_info=True)

    def _sync_viewport_height(self, _event=None):
        """Hace que Home ocupe todo el alto visible y mantenga su contenido centrado."""
        self._viewport_sync_job = None
        if not hasattr(self, "_parent_canvas") or not hasattr(self, "_create_window_id"):
            return
        try:
            canvas_height = self._parent_canvas.winfo_height()
            if canvas_height <= 1:
                return
            requested_height = self.winfo_reqheight()
            target_height = max(canvas_height, requested_height)
            self._parent_canvas.itemconfigure(self._create_window_id, height=target_height)
        except Exception:
            logger.debug("home.ui: viewport height sync omitido", exc_info=True)

    @stepwise
    def _build(self):
        """Construye accesos, información y paneles de la pantalla inicial."""
        self.grid_columnconfigure(0, weight=1)
        yield

        palette = styles.palette()
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        yield
        content.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")
        yield
        content.grid_columnconfigure((0, 1), weight=1, uniform="home-tools")
        yield

        header = ctk.CTkFrame(
            content, **styles.surface('panel'),
        )
        yield
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        yield
        header.grid_columnconfigure(0, weight=1)
        yield
        ctk.CTkLabel(
            header, text=t("app_title"), font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR, anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(16, 8), sticky="w")
        yield
        self._lbl_hint = ctk.CTkLabel(
            header, text=t("home_hint"), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor="w",
            wraplength=scale_wraplength(700), justify="left",
        )
        yield
        self._lbl_hint.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")
        yield

        self._header_links = ctk.CTkFrame(header, fg_color='transparent', corner_radius=0)
        yield
        self._header_links.grid(row=0, column=1, rowspan=2, padx=(8, 24), pady=16, sticky='e')
        yield
        self._website_icon = tintar_icono('assets/icons/globe.png', palette.text)
        yield
        if self._website_icon is not None:
            self._website_icon.configure(size=(30, 30))
            yield
        self._btn_website = ctk.CTkButton(
            self._header_links, text='', image=self._website_icon,
            width=44, height=44, corner_radius=0,
            fg_color='transparent', border_width=0, hover=False,
            cursor='hand2', command=open_project_page,
        )
        yield
        self._btn_website.grid(row=0, column=0, padx=(0, 8))
        yield
        self._github_icon = tintar_icono('assets/icons/github.png', palette.text)
        yield
        if self._github_icon is not None:
            self._github_icon.configure(size=(30, 30))
            yield
        self._btn_github = ctk.CTkButton(
            self._header_links, text='', image=self._github_icon,
            width=44, height=44, corner_radius=0,
            fg_color='transparent', border_width=0, hover=False,
            cursor='hand2', command=lambda: webbrowser.open(GITHUB_REPOSITORY_URL),
        )
        yield
        self._btn_github.grid(row=0, column=1)
        yield

        self._tool_buttons = []
        yield
        for index, spec in enumerate(iter_enabled_modules()):
            button = styles.Button(
                content,
                role='secondary', secondary_bg=palette.panel,
                text=t(spec.label_key),
                image=tintar_icono(spec.icon_path, palette.text),
                compound="left",
                anchor="w",
                height=58,
                border_spacing=16,
                font=fonts.FUENTE_BASE,
                command=lambda key=spec.key: self._seleccionar(key),
            )
            yield
            row = 1 + index // 2
            yield
            column = index % 2
            yield
            button.grid(
                row=row, column=column, padx=(0, 8) if column == 0 else (8, 0),
                pady=4, sticky="ew",
            )
            yield
            self._tool_buttons.append(button)
            yield

        self._btn_documentation = styles.Button(
            content, role='secondary', secondary_bg=palette.panel,
            text=t('documentation'),
            image=tintar_icono('assets/icons/book.png', palette.text),
            compound='left', anchor='w', height=58, border_spacing=16,
            font=fonts.FUENTE_BASE,
            command=lambda: open_project_page(documentation=True),
        )
        yield
        docs_column = len(self._tool_buttons) % 2
        yield
        self._btn_documentation.grid(
            row=1 + len(self._tool_buttons) // 2, column=docs_column,
            padx=(0, 8) if docs_column == 0 else (8, 0), pady=4, sticky='ew',
        )
        yield

        self._lbl_preload_errors = ctk.CTkLabel(
            content, text='',
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
        )
        yield

    def _seleccionar(self, key):
        """Solicita al módulo activo el archivo que eligió el usuario."""
        if callable(self._on_select):
            self._on_select(key)

    def show_preload_errors(self, labels):
        """Muestra los errores de módulos detectados durante el arranque."""
        self._lbl_preload_errors.configure(text=t('startup_partial').format(modules=labels),
                                           wraplength=600, justify='left')
        self._lbl_preload_errors.grid(
            row=1 + (len(self._tool_buttons) + 2) // 2,
            column=0, columnspan=2, pady=(16, 0), sticky='w',
        )
