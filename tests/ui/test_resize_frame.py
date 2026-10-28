"""Pruebas de interfaz para resize frame y sus estados principales."""

from app.ui.frames.resize.frame import ResizeFrame
from app import translations
import pytest


def test_resize_frame_build(ui_root):
    frame = ResizeFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_tab")
    assert hasattr(frame, "_frames")


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_result_uses_current_language(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
    frame = ResizeFrame(ui_root)
    for count in (0, 1, 2):
        frame._finalizar(frame._btn_canvas, 'Canvas', count, 0)
        noun = translations.t('image_loaded' if count == 1 else 'images_loaded')
        assert frame._lbl_info.cget('text').startswith(f'{count} {noun} ')
