"""Interfaz grafica para configurar ajustes de la aplicacion.

Tabs:
    - Ajustes
    - Actualizaciones
"""

from __future__ import annotations

import logging
import customtkinter as ctk
import webbrowser

from app.ui import colors, fonts
from app.utils import tintar_icono
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.settings.state import SettingsState
from app.ui.frames.settings.tabs.general_tab import GeneralTab
from app.ui.frames.settings.tabs.updates_tab import UpdatesTab


logger = logging.getLogger(__name__)

PAYPAL_DONATION_URL = 'https://paypal.me/guillebouix?locale.x=es_XC&country.x=AR'


class SettingsFrame(BaseFrame):
    """Frame principal del modulo de ajustes de la aplicacion."""

    def __init__(self, parent):
        logger.info("settings.ui: init")
        self._state = SettingsState()
        super().__init__(parent, t('settings_title'))

    def _build_content(self):
        logger.info("settings.ui: build_content")
        self.grid_columnconfigure(0, weight=1)
        self._add_donation_button()
        self._build_tabs()
        self._btn_limpiar.grid_remove()

    def _build_tabs(self):
        self._tab = ctk.CTkSegmentedButton(
            self,
            values=[t('settings_tab'), t('updates_tab')],
            font=fonts.FUENTE_BASE,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.PANEL_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_tab
        )
        self._tab.set(t('settings_tab'))
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 12), sticky='ew')

        self._tabs_container = ctk.CTkFrame(self, fg_color='transparent')
        self._tabs_container.grid(row=2, column=0, padx=28, pady=(0, 12), sticky='nsew')
        self._tabs_container.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        general_tab = GeneralTab(self._tabs_container, state=self._state, set_status=self._set_status)
        self._tabs = {
            t('settings_tab'): general_tab,
            t('updates_tab'): UpdatesTab(self._tabs_container),
        }
        self._selector_idioma = general_tab._selector_idioma
        self._selector_tema = general_tab._selector_tema
        self._selector_escala = general_tab._selector_escala
        for f in self._tabs.values():
            f.grid(row=0, column=0, sticky='nsew')

        self._cambiar_tab(t('settings_tab'))

    def _cambiar_tab(self, tab: str):
        for nombre, frame in self._tabs.items():
            if nombre == tab:
                frame.grid()
                frame.tkraise()
            else:
                frame.grid_remove()

    def _add_donation_button(self):
        logger.info("settings.ui: add_donation_button")
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

    def _set_status(self, text: str):
        self._lbl_info.configure(text=text)
