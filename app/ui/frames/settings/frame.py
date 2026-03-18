"""
UI para el modulo Ajustes / Settings.
Permite cambiar el idioma y otras configuraciones.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t, AVAILABLE_LANGUAGES
from app.ui.frames.base import BaseFrame
from app.ui.frames.settings.services import set_language_and_restart, set_theme_and_restart
from app.ui.frames.settings.state import SettingsState


class SettingsFrame(BaseFrame):
    def __init__(self, parent):
        self._state = SettingsState()
        super().__init__(parent, t('settings_title'))

    def _build_content(self):
        self.grid_columnconfigure(0, weight=1)

        # Panel de idioma
        panel_idioma = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_idioma.grid(row=1, column=0, padx=28, pady=16, sticky='ew')
        panel_idioma.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_idioma,
            text=t('language'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=16, sticky='w')

        self._selector_idioma = ctk.CTkOptionMenu(
            panel_idioma,
            values=list(AVAILABLE_LANGUAGES.keys()),
            variable=self._state.lang_var,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            command=self._cambiar_idioma
        )
        self._selector_idioma.grid(row=0, column=1, padx=(0, 16), pady=16, sticky='w')

        # Panel de tema
        panel_tema = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_tema.grid(row=2, column=0, padx=28, pady=(0, 16), sticky='ew')
        panel_tema.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_tema,
            text=t('ui_theme'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=16, sticky='w')

        self._selector_tema = ctk.CTkOptionMenu(
            panel_tema,
            values=colors.get_theme_names(),
            variable=self._state.theme_var,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            command=self._cambiar_tema
        )
        self._selector_tema.grid(row=0, column=1, padx=(0, 16), pady=16, sticky='w')

        # Oculta boton Limpiar del BaseFrame en settings
        self._btn_limpiar.grid_remove()

    def _cambiar_idioma(self, lang: str):
        """Cambia el idioma y reinicia la app."""
        self._lbl_info.configure(text=t('restart_required'))
        self.after(1500, lambda: set_language_and_restart(lang))

    def _cambiar_tema(self, theme: str):
        """Cambia el tema y reinicia la app."""
        self._lbl_info.configure(text=t('restart_required'))
        self.after(1500, lambda: set_theme_and_restart(theme))
