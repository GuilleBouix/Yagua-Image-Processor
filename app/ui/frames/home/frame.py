from __future__ import annotations

import logging

import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.ui.scale import scale_wraplength
from app.translations import t
from app.utils.paths import resource_path
from app.version import __version__


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
        self._build()
        self.after(0, self._bind_viewport_sync)

    def _bind_viewport_sync(self):
        """Mantiene la pantalla Home con al menos el alto del viewport visible."""
        if not hasattr(self, "_parent_canvas"):
            return
        try:
            self._parent_canvas.bind("<Configure>", self._sync_viewport_height, add="+")
            self.bind("<Configure>", self._sync_viewport_height, add="+")
            self._sync_viewport_height()
        except Exception:
            logger.exception("home.ui: no se pudo sincronizar viewport")

    def _sync_viewport_height(self, _event=None):
        """Hace que Home ocupe todo el alto visible y mantenga su contenido centrado."""
        if not hasattr(self, "_parent_canvas") or not hasattr(self, "_create_window_id"):
            return
        try:
            canvas_height = self._parent_canvas.winfo_height()
            requested_height = self.winfo_reqheight()
            target_height = max(canvas_height, requested_height)
            self._parent_canvas.itemconfigure(self._create_window_id, height=target_height)
        except Exception:
            logger.debug("home.ui: viewport height sync omitido", exc_info=True)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Contenedor centrado que ocupa todo el frame (sin "card", minimal).
        cont = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        cont.grid(row=0, column=0, sticky="nsew")
        cont.grid_columnconfigure(0, weight=1)
        cont.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(cont, fg_color="transparent", corner_radius=0)
        center.grid(row=0, column=0, sticky="nsew")
        center.grid_columnconfigure(0, weight=1)
        # Usamos filas flex para centrar verticalmente sin hacks de place()
        center.grid_rowconfigure(0, weight=1)
        center.grid_rowconfigure(4, weight=1)

        # Icono centrado
        icon_path = resource_path("assets/icon.png")
        icon_img = None
        try:
            img = Image.open(icon_path).convert("RGBA")
            icon_img = ctk.CTkImage(light_image=img, dark_image=img, size=(220, 220))
        except Exception as exc:
            logger.warning("home.ui: no se pudo cargar icon.png: %s", exc)

        self._lbl_icon = ctk.CTkLabel(center, text="", image=icon_img)
        self._lbl_icon.grid(row=1, column=0, padx=26, pady=(0, 10))

        # Versión (pequeña)
        self._lbl_version = ctk.CTkLabel(
            center,
            text=f"{t('current_version')}: v{__version__}",
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
        )
        self._lbl_version.grid(row=2, column=0, padx=26, pady=(0, 8))

        # Texto complementario breve
        self._lbl_hint = ctk.CTkLabel(
            center,
            text=t("home_hint"),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            justify="center",
            wraplength=scale_wraplength(720),
        )
        self._lbl_hint.grid(row=3, column=0, padx=30, pady=(0, 0))
