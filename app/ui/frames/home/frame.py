from __future__ import annotations

import logging

import customtkinter as ctk

from app.ui import colors, fonts
from app.ui.scale import scale_wraplength
from app.translations import t
from app.utils import tintar_icono
from app.version import __version__
from app.ui.module_registry import iter_enabled_modules


logger = logging.getLogger(__name__)


class HomeFrame(ctk.CTkScrollableFrame):
    """Pantalla inicial de bienvenida (solo visual)."""

    def __init__(self, parent):
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
        self._build()
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

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, padx=28, pady=(24, 28), sticky="nsew")
        content.grid_columnconfigure((0, 1), weight=1, uniform="home-tools")

        header = ctk.CTkFrame(
            content, corner_radius=12, fg_color=colors.PANEL_BG,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text=t("app_title"), font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR, anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(18, 5), sticky="w")
        self._lbl_hint = ctk.CTkLabel(
            header, text=t("home_hint"), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor="w",
            wraplength=scale_wraplength(700), justify="left",
        )
        self._lbl_hint.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        self._tool_buttons = []
        for index, spec in enumerate(iter_enabled_modules()):
            button = ctk.CTkButton(
                content,
                text=t(spec.label_key),
                image=tintar_icono(spec.icon_path, colors.ICON_COLOR),
                compound="left",
                anchor="w",
                height=58,
                corner_radius=9,
                border_width=1,
                border_color=colors.SIDEBAR_SEPARATOR,
                fg_color=colors.PANEL_BG,
                hover_color=colors.SIDEBAR_HOVER,
                text_color=colors.TEXT_COLOR,
                font=fonts.FUENTE_BASE,
                command=lambda key=spec.key: self._seleccionar(key),
            )
            row = 1 + index // 2
            column = index % 2
            button.grid(
                row=row, column=column, padx=(0, 8) if column == 0 else (8, 0),
                pady=5, sticky="ew",
            )
            self._tool_buttons.append(button)

        self._lbl_version = ctk.CTkLabel(
            content, text=f"{t('current_version')}: v{__version__}",
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
        )
        self._lbl_version.grid(
            row=1 + (len(self._tool_buttons) + 1) // 2,
            column=0, columnspan=2, pady=(14, 0), sticky="w",
        )

    def _seleccionar(self, key):
        if callable(self._on_select):
            self._on_select(key)
