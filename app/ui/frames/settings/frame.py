"""Interfaz grafica para configurar ajustes de la aplicacion.

Permite cambiar:
    - Idioma de la interfaz
    - Tema visual de la aplicacion

Ambos cambios requieren reiniciar la aplicacion para aplicarse.

Relaciones:
    - BaseFrame: app.ui.frames.base.BaseFrame
    - Traducciones: app.translations
    - Colores: app.ui.colors
    - Fuentes: app.ui.fonts
    - Servicios: app.ui.frames.settings.services
    - Estado: app.ui.frames.settings.state
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t, AVAILABLE_LANGUAGES
from app.ui.frames.base import BaseFrame
from app.ui.frames.settings.services import set_language_and_restart, set_theme_and_restart
from app.ui.frames.settings.state import SettingsState


class SettingsFrame(BaseFrame):
    """Frame principal del modulo de ajustes de la aplicacion."""

    def __init__(self, parent):
        self._state = SettingsState()
        super().__init__(parent, t('settings_title'))

    def _build_content(self):
        """Construir el contenido principal con paneles de idioma y tema."""
        self.grid_columnconfigure(0, weight=1)

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

        self._btn_limpiar.grid_remove()

    def _cambiar_idioma(self, lang: str):
        """Cambiar el idioma y reiniciar la aplicacion.

        Args:
            lang: Codigo de idioma seleccionado
        """
        self._lbl_info.configure(text=t('restart_required'))
        self.after(1500, lambda: set_language_and_restart(lang))

    def _cambiar_tema(self, theme: str):
        """Cambiar el tema y reiniciar la aplicacion.

        Args:
            theme: Nombre del tema seleccionado
        """
        self._lbl_info.configure(text=t('restart_required'))
        self.after(1500, lambda: set_theme_and_restart(theme))
