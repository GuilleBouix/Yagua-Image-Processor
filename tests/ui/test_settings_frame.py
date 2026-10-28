"""Pruebas de interfaz para settings frame y sus estados principales."""

import pytest
from app.translations import AVAILABLE_LANGUAGES
from app.ui.frames.settings.frame import SettingsFrame
from app.ui.frames.settings.tabs import general_tab as general_tab_module
from app.ui.frames.settings.tabs.general_tab import GeneralTab


def test_settings_frame_build(ui_root):
    frame = SettingsFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_selector_idioma")
    assert hasattr(frame, "_selector_tema")
    assert hasattr(frame, "_selector_escala")
    assert hasattr(frame, "_btn_apply")


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_settings_solo_aplica_al_presionar_boton(monkeypatch, ui_root, language):
    calls = []
    monkeypatch.setattr(
        general_tab_module,
        'apply_settings_and_restart',
        lambda **values: calls.append(values),
    )
    frame = SettingsFrame(ui_root)
    general = next(tab for tab in frame._tabs.values() if isinstance(tab, GeneralTab))
    monkeypatch.setattr(general, 'after', lambda _delay, callback: callback())

    assert general._selector_idioma.cget('values') == list(AVAILABLE_LANGUAGES)
    assert general._selector_idioma.cget('font').cget('family') in {'Noto Sans CJK JP', 'Noto Sans CJK SC'}
    assert general._selector_idioma.cget('dropdown_font').cget('family') in {'Noto Sans CJK JP', 'Noto Sans CJK SC'}
    general._selector_idioma.set(language)
    general._state.theme_var.set('Dracula')
    general._state.scale_var.set('75%')
    general._module_vars['ocr'].set(False)
    ui_root.update_idletasks()

    assert calls == []

    general._apply_settings()

    assert len(calls) == 1
    assert calls[0]['language'] == language
    assert calls[0]['theme'] == 'Dracula'
    assert calls[0]['ui_scale'] == 75
    assert 'ocr' not in calls[0]['visible_modules']
    assert 'settings' in calls[0]['visible_modules']
