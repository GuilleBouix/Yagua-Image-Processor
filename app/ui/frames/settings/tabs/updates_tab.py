"""Comprobación y descarga de actualizaciones publicadas en GitHub."""

from __future__ import annotations

from app.ui.building import finish, stepwise, steps_for
import logging
import threading
import webbrowser

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t
from app.version import __version__
from app.utils.update_checker import check_latest_update


logger = logging.getLogger(__name__)


class UpdatesTab(ctk.CTkFrame):
    """Tab Actualizaciones: solo check + link (sin auto-download/install)."""

    def _post_ui(self, delay, callback):
        """Encola una actualización para aplicarla en el hilo principal de Tk."""
        from app.ui.operations import operations
        operations.post(self, callback)

    def __init__(self, parent, *, defer_build=False):
        """Inicializa el estado de búsqueda y descarga de versiones."""
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._worker_activo = False
        self._download_url: str | None = None
        self._build_iterator = steps_for(self._build)
        if not defer_build:
            finish(self._build_iterator)

    @stepwise
    def _build(self):
        """Construye controles para buscar, descargar y abrir la publicación."""
        panel = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        yield
        panel.grid(row=0, column=0, sticky="ew")
        yield
        panel.grid_columnconfigure(0, weight=1)
        yield

        ctk.CTkLabel(
            panel,
            text=t("updates_title"),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")
        yield

        self._lbl_update_status = ctk.CTkLabel(
            panel,
            text=t("no_updates"),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor="w",
        )
        yield
        self._lbl_update_status.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")
        yield

        self._btn_check_updates = styles.Button(
            panel,
            role='primary',
            text=t("check_updates"),
            width=180,
            height=40,
            font=fonts.FUENTE_BASE,
            command=self._check_updates,
        )
        yield
        self._btn_check_updates.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")
        yield

        # Botón de descarga (se muestra solo si hay update)
        self._btn_download = styles.Button(
            panel,
            text=t("updates_download_btn").format(version=""),  # type: ignore
            width=260,
            height=40,
            font=fonts.FUENTE_BASE,
            command=self._abrir_release,
        )
        yield
        self._btn_download.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="w")
        yield
        self._btn_download.grid_remove()
        yield

        self._lbl_manual = ctk.CTkLabel(
            panel,
            text=t("updates_manual_hint"),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor="w",
        )
        yield
        self._lbl_manual.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="w")
        yield
        self._lbl_manual.grid_remove()
        yield

    def _set_status(self, text: str):
        """Actualiza el mensaje de estado de la pestaña."""
        if self._lbl_update_status.winfo_exists():
            self._lbl_update_status.configure(text=text)

    def _set_busy(self, busy: bool):
        """Bloquea o habilita controles según el trabajo en curso."""
        self._worker_activo = busy
        if self._btn_check_updates.winfo_exists():
            self._btn_check_updates.configure(state="disabled" if busy else "normal")

    def _mostrar_descarga(self, version: str, url: str):
        """Presenta la descarga disponible para la versión detectada."""
        self._download_url = url
        if self._btn_download.winfo_exists():
            self._btn_download.configure(text=t("updates_download_btn").format(version=version))  # type: ignore
            self._btn_download.grid()
        if self._lbl_manual.winfo_exists():
            self._lbl_manual.grid()

    def _ocultar_descarga(self):
        """Retira los controles de descarga cuando dejan de aplicar."""
        self._download_url = None
        if self._btn_download.winfo_exists():
            self._btn_download.grid_remove()
        if self._lbl_manual.winfo_exists():
            self._lbl_manual.grid_remove()

    def _abrir_release(self):
        """Abre la publicación seleccionada en el navegador predeterminado."""
        if not self._download_url:
            return
        try:
            webbrowser.open(self._download_url)
        except Exception:
            logger.exception("updates: no se pudo abrir el navegador")

    def _check_updates(self):
        """Inicia una consulta de versiones y controla el estado ocupado."""
        if self._worker_activo:
            return

        self._set_busy(True)
        self._set_status(t("updates_checking"))
        self._ocultar_descarga()

        def _worker():
            """Consulta o descarga datos sin leer widgets desde el worker."""
            try:
                info = check_latest_update(__version__)
                if not info:
                    self._post_ui(0, lambda: self._set_status(t("no_updates")))
                    return
                self._post_ui(0, lambda: self._set_status(t("updates_available").format(version=info.version)))  # type: ignore
                self._post_ui(0, lambda: self._mostrar_descarga(info.version, info.release_url))
            except Exception:
                logger.exception("updates: error")
                self._post_ui(0, lambda: self._set_status(t("updates_error")))
            finally:
                self._post_ui(0, lambda: self._set_busy(False))

        threading.Thread(target=_worker, daemon=True).start()

