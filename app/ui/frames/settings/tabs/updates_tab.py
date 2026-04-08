from __future__ import annotations

import logging
import threading
import webbrowser

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.version import __version__
from app.utils.update_checker import check_latest_stable


logger = logging.getLogger(__name__)


class UpdatesTab(ctk.CTkFrame):
    """Tab Actualizaciones: solo check + link (sin auto-download/install)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._worker_activo = False
        self._download_url: str | None = None
        self._build()

    def _build(self):
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
        )
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=t("updates_title"),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        self._lbl_version = ctk.CTkLabel(
            panel,
            text=f"{t('current_version')}: v{__version__}",
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor="w",
        )
        self._lbl_version.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="w")

        self._lbl_update_status = ctk.CTkLabel(
            panel,
            text=t("no_updates"),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor="w",
        )
        self._lbl_update_status.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")

        self._btn_check_updates = ctk.CTkButton(
            panel,
            text=t("check_updates"),
            width=180,
            height=34,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._check_updates,
        )
        self._btn_check_updates.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="w")

        # Botón de descarga (se muestra solo si hay update)
        self._btn_download = ctk.CTkButton(
            panel,
            text=t("updates_download_btn").format(version=""),  # type: ignore
            width=260,
            height=34,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._abrir_release,
        )
        self._btn_download.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="w")
        self._btn_download.grid_remove()

        self._lbl_manual = ctk.CTkLabel(
            panel,
            text=t("updates_manual_hint"),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor="w",
        )
        self._lbl_manual.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="w")
        self._lbl_manual.grid_remove()

    def _set_status(self, text: str):
        if self._lbl_update_status.winfo_exists():
            self._lbl_update_status.configure(text=text)

    def _set_busy(self, busy: bool):
        self._worker_activo = busy
        if self._btn_check_updates.winfo_exists():
            self._btn_check_updates.configure(state="disabled" if busy else "normal")

    def _mostrar_descarga(self, version: str, url: str):
        self._download_url = url
        if self._btn_download.winfo_exists():
            self._btn_download.configure(text=t("updates_download_btn").format(version=version))  # type: ignore
            self._btn_download.grid()
        if self._lbl_manual.winfo_exists():
            self._lbl_manual.grid()

    def _ocultar_descarga(self):
        self._download_url = None
        if self._btn_download.winfo_exists():
            self._btn_download.grid_remove()
        if self._lbl_manual.winfo_exists():
            self._lbl_manual.grid_remove()

    def _abrir_release(self):
        if not self._download_url:
            return
        try:
            webbrowser.open(self._download_url)
        except Exception:
            logger.exception("updates: no se pudo abrir el navegador")

    def _check_updates(self):
        if self._worker_activo:
            return

        self._set_busy(True)
        self._set_status(t("updates_checking"))
        self._ocultar_descarga()

        def _worker():
            try:
                info = check_latest_stable(__version__)
                if not info:
                    self.after(0, lambda: self._set_status(t("no_updates")))
                    return
                self.after(0, lambda: self._set_status(t("updates_available").format(version=info.version)))  # type: ignore
                self.after(0, lambda: self._mostrar_descarga(info.version, info.release_url))
            except Exception:
                logger.exception("updates: error")
                self.after(0, lambda: self._set_status(t("updates_error")))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=_worker, daemon=True).start()

