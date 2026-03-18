"""
Definicion de paletas de colores del proyecto.
Usa estas constantes en toda la aplicacion para mantener consistencia.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_THEME = 'Default'

THEMES: dict[str, dict[str, str]] = {
    'Default': {
        # Fondos
        'FRAMES_BG': '#0A0A0B',
        'SIDEBAR_BG': '#121214',
        'PANEL_BG': '#1C1C1E',
        'SIDEBAR_SEPARATOR': '#2C2C2E',
        # Interaccion
        'SIDEBAR_HOVER': '#2C2C2E',
        'SIDEBAR_ACTIVE': '#FFFFFF',
        'SIDEBAR_ACTIVE_HOVER': '#E5E5EA',
        # Drop zone
        'DROPZONE_BORDER': '#3A3A3C',
        'DROPZONE_BG': '#0F0F11',
        # Texto
        'TEXT_COLOR': '#F2F2F7',
        'TEXT_GRAY': '#8E8E93',
        'TEXT_HOVER': '#000000',
        'TEXT_ACTIVE': '#000000',
        # Iconos
        'ICON_COLOR': '#E5E5EA',
        'ICON_COLOR_ACTIVE': '#000000',
        # Acentos
        'ACENTO': '#FFFFFF',
        'ACENTO_HOVER': '#D1D1D6',
        'ACENTO_DIMMED': '#48484A',
        # Controles
        'BTN_CLEAR_BG': '#FFFFFF',
        'BTN_CLEAR_TEXT': '#1A1A1A',
        'BTN_CLEAR_HOVER': '#EEEEEE',
        'SEGMENT_SELECTED': '#949494',
        'SEGMENT_SELECTED_HOVER': '#949494',
    },
    'Tokyo Night': {
        'FRAMES_BG': '#1A1B26',
        'SIDEBAR_BG': '#16161E',
        'PANEL_BG': '#1F2335',
        'SIDEBAR_SEPARATOR': '#2A2F41',
        'SIDEBAR_HOVER': '#2A2F41',
        'SIDEBAR_ACTIVE': '#2F3549',
        'SIDEBAR_ACTIVE_HOVER': '#3A405A',
        'DROPZONE_BORDER': '#2A2F41',
        'DROPZONE_BG': '#171821',
        'TEXT_COLOR': '#C0CAF5',
        'TEXT_GRAY': '#7AA2F7',
        'TEXT_HOVER': '#C0CAF5',
        'TEXT_ACTIVE': '#C0CAF5',
        'ICON_COLOR': '#A9B1D6',
        'ICON_COLOR_ACTIVE': '#C0CAF5',
        'ACENTO': '#7AA2F7',
        'ACENTO_HOVER': '#5D7BD3',
        'ACENTO_DIMMED': '#3B4261',
        'BTN_CLEAR_BG': '#7AA2F7',
        'BTN_CLEAR_TEXT': '#1A1B26',
        'BTN_CLEAR_HOVER': '#6C8DE0',
        'SEGMENT_SELECTED': '#3B4261',
        'SEGMENT_SELECTED_HOVER': '#3B4261',
    },
    'Dracula': {
        'FRAMES_BG': '#1E1F29',
        'SIDEBAR_BG': '#1B1C26',
        'PANEL_BG': '#232533',
        'SIDEBAR_SEPARATOR': '#303245',
        'SIDEBAR_HOVER': '#303245',
        'SIDEBAR_ACTIVE': '#2B2E3F',
        'SIDEBAR_ACTIVE_HOVER': '#3A3D55',
        'DROPZONE_BORDER': '#3A3D55',
        'DROPZONE_BG': '#1D1E28',
        'TEXT_COLOR': '#F8F8F2',
        'TEXT_GRAY': '#9CA2D7',
        'TEXT_HOVER': '#F8F8F2',
        'TEXT_ACTIVE': '#F8F8F2',
        'ICON_COLOR': '#C7CBEF',
        'ICON_COLOR_ACTIVE': '#F8F8F2',
        'ACENTO': '#BD93F9',
        'ACENTO_HOVER': '#9A6BE8',
        'ACENTO_DIMMED': '#44475A',
        'BTN_CLEAR_BG': '#BD93F9',
        'BTN_CLEAR_TEXT': '#1E1F29',
        'BTN_CLEAR_HOVER': '#A778E6',
        'SEGMENT_SELECTED': '#44475A',
        'SEGMENT_SELECTED_HOVER': '#44475A',
    },
    'Nord': {
        'FRAMES_BG': '#2E3440',
        'SIDEBAR_BG': '#2B303B',
        'PANEL_BG': '#343B49',
        'SIDEBAR_SEPARATOR': '#3B4252',
        'SIDEBAR_HOVER': '#3B4252',
        'SIDEBAR_ACTIVE': '#3E4759',
        'SIDEBAR_ACTIVE_HOVER': '#465063',
        'DROPZONE_BORDER': '#4C566A',
        'DROPZONE_BG': '#2C313C',
        'TEXT_COLOR': '#ECEFF4',
        'TEXT_GRAY': '#A3B0C8',
        'TEXT_HOVER': '#ECEFF4',
        'TEXT_ACTIVE': '#ECEFF4',
        'ICON_COLOR': '#D8DEE9',
        'ICON_COLOR_ACTIVE': '#ECEFF4',
        'ACENTO': '#81A1C1',
        'ACENTO_HOVER': '#6C8FB3',
        'ACENTO_DIMMED': '#4C566A',
        'BTN_CLEAR_BG': '#81A1C1',
        'BTN_CLEAR_TEXT': '#2E3440',
        'BTN_CLEAR_HOVER': '#6F92B4',
        'SEGMENT_SELECTED': '#4C566A',
        'SEGMENT_SELECTED_HOVER': '#4C566A',
    },
}

_CURRENT_THEME = DEFAULT_THEME

# Declare module-level names for type checkers
FRAMES_BG = THEMES[DEFAULT_THEME]['FRAMES_BG']
SIDEBAR_BG = THEMES[DEFAULT_THEME]['SIDEBAR_BG']
PANEL_BG = THEMES[DEFAULT_THEME]['PANEL_BG']
SIDEBAR_SEPARATOR = THEMES[DEFAULT_THEME]['SIDEBAR_SEPARATOR']
SIDEBAR_HOVER = THEMES[DEFAULT_THEME]['SIDEBAR_HOVER']
SIDEBAR_ACTIVE = THEMES[DEFAULT_THEME]['SIDEBAR_ACTIVE']
SIDEBAR_ACTIVE_HOVER = THEMES[DEFAULT_THEME]['SIDEBAR_ACTIVE_HOVER']
DROPZONE_BORDER = THEMES[DEFAULT_THEME]['DROPZONE_BORDER']
DROPZONE_BG = THEMES[DEFAULT_THEME]['DROPZONE_BG']
TEXT_COLOR = THEMES[DEFAULT_THEME]['TEXT_COLOR']
TEXT_GRAY = THEMES[DEFAULT_THEME]['TEXT_GRAY']
TEXT_HOVER = THEMES[DEFAULT_THEME]['TEXT_HOVER']
TEXT_ACTIVE = THEMES[DEFAULT_THEME]['TEXT_ACTIVE']
ICON_COLOR = THEMES[DEFAULT_THEME]['ICON_COLOR']
ICON_COLOR_ACTIVE = THEMES[DEFAULT_THEME]['ICON_COLOR_ACTIVE']
ACENTO = THEMES[DEFAULT_THEME]['ACENTO']
ACENTO_HOVER = THEMES[DEFAULT_THEME]['ACENTO_HOVER']
ACENTO_DIMMED = THEMES[DEFAULT_THEME]['ACENTO_DIMMED']
BTN_CLEAR_BG = THEMES[DEFAULT_THEME]['BTN_CLEAR_BG']
BTN_CLEAR_TEXT = THEMES[DEFAULT_THEME]['BTN_CLEAR_TEXT']
BTN_CLEAR_HOVER = THEMES[DEFAULT_THEME]['BTN_CLEAR_HOVER']
SEGMENT_SELECTED = THEMES[DEFAULT_THEME]['SEGMENT_SELECTED']
SEGMENT_SELECTED_HOVER = THEMES[DEFAULT_THEME]['SEGMENT_SELECTED_HOVER']


def _settings_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'user_settings.json'


def _load_theme() -> str:
    path = _settings_path()
    if not path.exists():
        return DEFAULT_THEME
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        theme = data.get('theme')
        return theme if theme in THEMES else DEFAULT_THEME
    except Exception:
        return DEFAULT_THEME


def apply_theme(theme_name: str) -> None:
    global _CURRENT_THEME
    theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    _CURRENT_THEME = theme_name if theme_name in THEMES else DEFAULT_THEME
    for key, value in theme.items():
        globals()[key] = value


def get_theme_names() -> list[str]:
    return list(THEMES.keys())


def get_current_theme() -> str:
    return _CURRENT_THEME


apply_theme(_load_theme())
