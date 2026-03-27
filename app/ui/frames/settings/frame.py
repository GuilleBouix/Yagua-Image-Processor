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
import webbrowser

from app.ui import colors, fonts
from app.utils import tintar_icono
from app.translations import t, AVAILABLE_LANGUAGES
from app.ui.frames.base import BaseFrame
from app.ui.frames.settings.services import (
    set_language_and_restart,
    set_theme_and_restart,
    get_visible_modules,
    set_visible_modules_and_restart,
)
from app.ui.frames.settings.state import SettingsState
from app.ui.module_registry import iter_all_modules

PAYPAL_DONATION_URL = 'https://paypal.me/guillebouix?locale.x=es_XC&country.x=AR'

class SettingsFrame(BaseFrame):
    """Frame principal del modulo de ajustes de la aplicacion."""

    def __init__(self, parent):
        self._state = SettingsState()
        super().__init__(parent, t('settings_title'))

    def _build_content(self):
        """Construir el contenido principal con paneles de idioma y tema."""
        self.grid_columnconfigure(0, weight=1)
        self._add_donation_button()

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

        self._build_modules_panel()
        self._btn_limpiar.grid_remove()

    def _add_donation_button(self):
        """Agregar boton de donacion junto al titulo."""
        if not hasattr(self, '_title_row') or not self._title_row.winfo_exists():
            return
        icon_donar = tintar_icono('assets/icons/heart.png', '#000000')
        btn = ctk.CTkButton(
            self._title_row,
            text=t('donate_paypal_btn'),
            image=icon_donar,
            compound='left',
            width=150,
            height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=lambda: webbrowser.open(PAYPAL_DONATION_URL)
        )
        btn.grid(row=0, column=2, padx=(8, 0), sticky='e')

    def _build_modules_panel(self):
        """Panel para seleccionar modulos visibles en la sidebar."""
        panel_modulos = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_modulos.grid(row=3, column=0, padx=28, pady=(0, 16), sticky='ew')
        panel_modulos.grid_columnconfigure(0, weight=1)
        panel_modulos.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_modulos,
            text=t('visible_modules'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 6), sticky='w')

        ctk.CTkLabel(
            panel_modulos,
            text=t('visible_modules_hint'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=1, column=0, columnspan=2, padx=(16, 12), pady=(0, 10), sticky='w')

        visibles = get_visible_modules()
        if not visibles:
            visibles = [m.key for m in iter_all_modules()]
        visibles_set = set(visibles)
        visibles_set.add('settings')

        self._module_vars = {}
        start_row = 2
        for idx, spec in enumerate(iter_all_modules()):
            is_settings = spec.key == 'settings'
            var = ctk.BooleanVar(value=(spec.key in visibles_set))
            self._module_vars[spec.key] = var

            switch = ctk.CTkSwitch(
                panel_modulos,
                text=t(spec.label_key),
                variable=var,
                onvalue=True,
                offvalue=False,
                text_color=colors.TEXT_COLOR,
                fg_color=colors.SIDEBAR_SEPARATOR,
                progress_color=colors.ACENTO,
                button_color=colors.SIDEBAR_BG,
                button_hover_color=colors.SIDEBAR_HOVER,
            )
            if is_settings:
                switch.configure(state='disabled')
            row = start_row + (idx // 2)
            col = idx % 2
            pad_left = (16, 12) if col == 0 else (8, 12)
            switch.grid(row=row, column=col, padx=pad_left, pady=6, sticky='w')

        self._btn_apply_modules = ctk.CTkButton(
            panel_modulos,
            text=t('apply_changes'),
            width=120,
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=self._apply_modules
        )
        last_row = start_row + ((idx) // 2 if 'idx' in locals() else 0) + 1
        self._btn_apply_modules.grid(row=last_row, column=0, columnspan=2, padx=16, pady=(8, 14), sticky='w')

    def _apply_modules(self):
        """Guardar modulos visibles y reiniciar."""
        visibles = [k for k, v in self._module_vars.items() if v.get()]
        if 'settings' not in visibles:
            visibles.append('settings')
        self._lbl_info.configure(text=t('restart_required_generic'))
        self.after(1500, lambda: set_visible_modules_and_restart(visibles))

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
