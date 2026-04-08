from __future__ import annotations

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.version import __version__


class UpdatesTab(ctk.CTkFrame):
    """Tab Actualizaciones: UI placeholder."""

    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=0, column=0, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text=t('updates_title'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky='w')

        self._lbl_version = ctk.CTkLabel(
            panel,
            text=f"{t('current_version')}: v{__version__}",
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        )
        self._lbl_version.grid(row=1, column=0, padx=16, pady=(0, 6), sticky='w')

        self._lbl_update_status = ctk.CTkLabel(
            panel,
            text=t('no_updates'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        )
        self._lbl_update_status.grid(row=2, column=0, padx=16, pady=(0, 12), sticky='w')

        self._btn_check_updates = ctk.CTkButton(
            panel,
            text=t('check_updates'),
            width=160,
            height=34,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._check_updates_placeholder
        )
        self._btn_check_updates.grid(row=3, column=0, padx=16, pady=(0, 16), sticky='w')

    def _check_updates_placeholder(self):
        self._lbl_update_status.configure(text=t('no_updates'))
