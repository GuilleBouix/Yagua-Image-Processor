from __future__ import annotations

import logging
import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t, AVAILABLE_LANGUAGES
from app.ui.module_registry import iter_all_modules
from app.ui.frames.settings.services import (
    apply_settings_and_restart,
    get_visible_modules,
)

logger = logging.getLogger(__name__)


class GeneralTab(ctk.CTkFrame):
    """Tab Ajustes: idioma, tema, modulos visibles."""

    def __init__(self, parent, *, state, set_status):
        super().__init__(parent, fg_color='transparent')
        self._state = state
        self._set_status = set_status
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        panel_idioma = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_idioma.grid(row=0, column=0, pady=(0, 12), sticky='ew')
        panel_idioma.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_idioma,
            text=t('language'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=16, sticky='w')

        language_font = fonts.fuente_selector_idiomas()
        self._selector_idioma = ctk.CTkOptionMenu(
            panel_idioma,
            values=list(AVAILABLE_LANGUAGES.keys()),
            variable=self._state.lang_var,
            font=language_font,
            dropdown_font=language_font,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
        )
        self._selector_idioma.grid(row=0, column=1, padx=(0, 16), pady=16, sticky='w')

        panel_tema = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_tema.grid(row=1, column=0, pady=(0, 12), sticky='ew')
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
        )
        self._selector_tema.grid(row=0, column=1, padx=(0, 16), pady=16, sticky='w')

        self._build_scale_panel(row=2)
        self._build_modules_panel(row=3)
        self._build_apply_button(row=4)

    def _build_scale_panel(self, row=0):
        panel_scale = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_scale.grid(row=row, column=0, pady=(0, 12), sticky='ew')
        panel_scale.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_scale,
            text=t('ui_scale'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 6), sticky='w')

        self._selector_escala = ctk.CTkSegmentedButton(
            panel_scale,
            values=['100%', '75%', '50%'],
            variable=self._state.scale_var,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
        )
        self._selector_escala.grid(row=0, column=1, padx=(0, 16), pady=(16, 6), sticky='w')

        ctk.CTkLabel(
            panel_scale,
            text=t('ui_scale_hint'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=1, column=0, columnspan=2, padx=(16, 12), pady=(0, 16), sticky='w')

    def _build_modules_panel(self, row=0):
        panel_modulos = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_modulos.grid(row=row, column=0, pady=(0, 16), sticky='ew')
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

    def _build_apply_button(self, row=0):
        self._btn_apply = ctk.CTkButton(
            self,
            text=t('apply_changes'),
            width=120,
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=self._apply_settings,
        )
        self._btn_apply.grid(row=row, column=0, pady=(0, 16), sticky='w')

    def _apply_settings(self):
        if self._btn_apply.cget('state') == 'disabled':
            return
        visibles = [k for k, v in self._module_vars.items() if v.get()]
        if 'settings' not in visibles:
            visibles.append('settings')
        language = self._state.lang_var.get()
        theme = self._state.theme_var.get()
        scale_label = self._state.scale_var.get()
        try:
            scale = int(scale_label.rstrip('%'))
        except ValueError:
            scale = 100
        logger.info(
            "settings.ui: apply (language=%s, theme=%s, scale=%s)",
            language,
            theme,
            scale,
        )
        self._set_status(t('restart_required_generic'))
        self._btn_apply.configure(state='disabled')
        self.after(
            1500,
            lambda: self._save_and_restart(
                language=language,
                theme=theme,
                ui_scale=scale,
                visible_modules=visibles,
            ),
        )


    def _save_and_restart(self, **options):
        if not self.winfo_exists():
            return
        try:
            apply_settings_and_restart(**options)
        except Exception as error:
            self._set_status(f"{t('error_generic')}: {error}")
        finally:
            if self.winfo_exists():
                self._btn_apply.configure(state='normal')
