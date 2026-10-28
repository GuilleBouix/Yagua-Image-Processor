"""Pruebas de interfaz para fonts y sus estados principales."""

import sys
import tkinter.font as tkfont

import customtkinter as ctk
import pytest

from app.ui import fonts
from app.languages import AVAILABLE_LANGUAGES
from app.utils import package_selftest


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_real_font_registration_and_widget_defaults(ui_root, monkeypatch, language):
    if sys.platform not in ('win32', 'linux'):
        pytest.skip('Private font registration is supported on Windows and Linux')
    assert all(fonts.registrar_fuentes().values())
    report = package_selftest._verify_ui_fonts(ui_root)
    assert report['font_bytes'] == 66939968
    assert report['families'] == ['Inter', 'Noto Sans CJK JP', 'Noto Sans CJK SC']
    for name in ('FUENTE_BASE', 'FUENTE_TITULO', 'FUENTE_CHICA'):
        monkeypatch.setattr(fonts, name, getattr(fonts, name))
    monkeypatch.setitem(ctk.ThemeManager.theme['CTkFont'], 'family', ctk.ThemeManager.theme['CTkFont']['family'])
    fonts.inicializar_fuentes(language)
    family = fonts.LANGUAGE_FAMILIES.get(language, 'Inter')
    assert family in tkfont.families(ui_root)
    assert fonts.FUENTE_BASE.actual('family') == family
    assert fonts.FUENTE_TITULO.actual('family') == family
    assert fonts.FUENTE_TITULO.actual('weight') == 'bold'
    button = ctk.CTkButton(ui_root, text='日本語 简体中文 Русский')
    menu = ctk.CTkOptionMenu(ui_root, values=list(AVAILABLE_LANGUAGES))
    assert button.cget('font').cget('family') == family
    assert menu.cget('dropdown_font').cget('family') == family
    button.destroy()
    menu.destroy()


def test_package_probe_rejects_missing_ui_font(ui_root, monkeypatch):
    monkeypatch.setattr(fonts, 'registrar_fuentes', lambda: {'missing.otf': False})
    with pytest.raises(RuntimeError, match='font registration failed'):
        package_selftest._verify_ui_fonts(ui_root)


def test_package_probe_rejects_missing_tk_font_family(ui_root, monkeypatch):
    monkeypatch.setattr(fonts, 'registrar_fuentes', lambda: {'font.otf': True})
    monkeypatch.setattr(tkfont, 'families', lambda app: ('Inter',))
    with pytest.raises(RuntimeError, match='font families unavailable'):
        package_selftest._verify_ui_fonts(ui_root)
