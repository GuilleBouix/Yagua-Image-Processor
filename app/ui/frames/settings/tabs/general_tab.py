"""Preferencias generales de idioma, escala, módulos y acciones de la aplicación."""

from __future__ import annotations

from app.ui.building import finish, stepwise, steps_for
import logging
import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t, AVAILABLE_LANGUAGES
from app.ui.module_registry import iter_all_modules
from app.ui.frames.settings.services import (
    apply_settings_and_restart,
    get_visible_modules,
)
from app.ui.frames.settings.legal_panel import LegalPanel

logger = logging.getLogger(__name__)


class GeneralTab(ctk.CTkFrame):
    """Tab Ajustes: idioma, tema, modulos visibles."""

    def __init__(self, parent, *, state, set_status, defer_build=False):
        """Conecta ajustes editables con los servicios de preferencias."""
        super().__init__(parent, fg_color='transparent')
        self._state = state
        self._set_status = set_status
        self.grid_columnconfigure(0, weight=1)
        self._build_iterator = steps_for(self._build)
        if not defer_build:
            finish(self._build_iterator)

    @stepwise
    def _build(self):
        """Construye los controles de configuración general."""
        panel_idioma = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        yield
        panel_idioma.grid(row=0, column=0, pady=(0, 12), sticky='ew')
        yield
        panel_idioma.grid_columnconfigure(1, weight=1)
        yield

        ctk.CTkLabel(
            panel_idioma,
            text=t('language'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=16, sticky='w')
        yield

        language_font = fonts.fuente_selector_idiomas()
        yield
        language_field = styles.OptionField(
            panel_idioma,
            width=140,
            values=list(AVAILABLE_LANGUAGES.keys()),
            variable=self._state.lang_var,
            font=language_font,
            dropdown_font=language_font,
        )
        yield
        self._selector_idioma = language_field.menu
        language_field.grid(row=0, column=1, padx=(0, 16), pady=16, sticky='w')
        yield

        panel_tema = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        yield
        panel_tema.grid(row=1, column=0, pady=(0, 12), sticky='ew')
        yield
        panel_tema.grid_columnconfigure((0, 1), weight=1, uniform='appearance')
        yield

        ctk.CTkLabel(
            panel_tema,
            text=t('ui_theme'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky='w')
        yield

        theme_field = styles.OptionField(
            panel_tema,
            width=140,
            values=colors.get_theme_names(),
            variable=self._state.theme_var,
            font=fonts.FUENTE_BASE,
        )
        yield
        self._selector_tema = theme_field.menu
        theme_field.grid(row=1, column=0, padx=16, pady=(0, 6), sticky='w')
        yield

        (yield from steps_for(self._build_scale_panel, panel_tema))
        yield
        (yield from steps_for(self._build_modules_panel, row=2))
        yield
        (yield from steps_for(self._build_apply_button, row=3))
        yield
        LegalPanel(self, set_status=self._set_status).grid(
            row=4, column=0, pady=(0, 16), sticky='ew')
        yield

    @stepwise
    def _build_scale_panel(self, panel_scale):
        """Agrega opciones de escala de interfaz y sus ayudas."""
        ctk.CTkLabel(
            panel_scale,
            text=t('ui_scale'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=1, padx=16, pady=(12, 4), sticky='w')
        yield

        self._selector_escala = styles.SegmentedButton(
            panel_scale,
            values=['100%', '75%', '50%'],
            variable=self._state.scale_var,
            font=fonts.FUENTE_CHICA,
        )
        yield
        self._selector_escala.grid(row=1, column=1, padx=16, pady=(0, 6), sticky='w')
        yield

        hint = ctk.CTkLabel(
            panel_scale,
            text=t('ui_scale_hint'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w', justify='left', width=1, wraplength=500,
        )
        yield
        hint.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 12), sticky='ew')
        yield

        def fit_hint(event):
            """Ajusta las ayudas al ancho de ventana sin cortar su contenido."""
            width = max(120, int(event.width / panel_scale._get_widget_scaling()) - 32)
            if hint.cget('wraplength') != width:
                hint.configure(wraplength=width)

        panel_scale.bind('<Configure>', fit_hint, add=True)
        yield

    @stepwise
    def _build_modules_panel(self, row=0):
        """Muestra interruptores para módulos disponibles."""
        panel_modulos = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        yield
        panel_modulos.grid(row=row, column=0, pady=(0, 16), sticky='ew')
        yield
        panel_modulos.grid_columnconfigure(0, weight=1)
        yield
        panel_modulos.grid_columnconfigure(1, weight=1)
        yield

        ctk.CTkLabel(
            panel_modulos,
            text=t('visible_modules'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 6), sticky='w')
        yield

        ctk.CTkLabel(
            panel_modulos,
            text=t('visible_modules_hint'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=1, column=0, columnspan=2, padx=(16, 12), pady=(0, 10), sticky='w')
        yield

        visibles = get_visible_modules()
        yield
        if not visibles:
            visibles = [m.key for m in iter_all_modules()]
            yield
        visibles_set = set(visibles)
        yield
        visibles_set.add('settings')
        yield

        self._module_vars = {}
        yield
        start_row = 2
        yield
        for idx, spec in enumerate(iter_all_modules()):
            is_settings = spec.key == 'settings'
            yield
            var = ctk.BooleanVar(value=(spec.key in visibles_set))
            yield
            self._module_vars[spec.key] = var
            yield

            switch = styles.Switch(
                panel_modulos,
                text=t(spec.label_key),
                variable=var,
                onvalue=True,
                offvalue=False,
            )
            yield
            if is_settings:
                switch.configure(state='disabled')
                yield
            row = start_row + (idx // 2)
            yield
            col = idx % 2
            yield
            pad_left = (16, 12) if col == 0 else (8, 12)
            yield
            switch.grid(row=row, column=col, padx=pad_left, pady=6, sticky='w')
            yield

    @stepwise
    def _build_apply_button(self, row=0):
        """Crea la acción que guarda cambios y solicita reiniciar."""
        self._btn_apply = styles.Button(
            self,
            role='primary',
            text=t('apply_changes'),
            width=120,
            height=40,
            font=fonts.FUENTE_CHICA,
            command=self._apply_settings,
        )
        yield
        self._btn_apply.grid(row=row, column=0, pady=(0, 16), sticky='w')
        yield

    def _apply_settings(self):
        """Valida y persiste cambios sin aplicarlos a medias."""
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
        """Guarda preferencias y programa un reinicio seguro de la aplicación."""
        if not self.winfo_exists():
            return
        try:
            apply_settings_and_restart(**options)
        except Exception as error:
            self._set_status(f"{t('error_generic')}: {error}")
        finally:
            if self.winfo_exists():
                self._btn_apply.configure(state='normal')
