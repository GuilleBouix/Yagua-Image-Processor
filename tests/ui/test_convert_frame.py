"""Pruebas de interfaz para convert frame y sus estados principales."""

from app.ui.frames.convert.frame import ConvertFrame
from app import translations
import pytest


def test_convert_frame_build(ui_root):
    frame = ConvertFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_panel_opciones")
    assert hasattr(frame, "_seg_formato")
    assert hasattr(frame, "_btn_convertir")


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_result_uses_current_language(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
    frame = ConvertFrame(ui_root)
    for count in (0, 1, 2):
        frame._finalizar(count, 0, 'PNG')
        noun = translations.t('image_loaded' if count == 1 else 'images_loaded')
        assert frame._lbl_info.cget('text').startswith(f'{count} {noun} ')
