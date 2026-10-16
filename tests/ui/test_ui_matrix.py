"""Construction/navigation coverage; visual clipping remains a manual acceptance check."""
import pytest
import customtkinter as ctk
from app import translations
from app.ui import colors, fonts
from app.ui.module_registry import iter_all_modules, load_frame_class
from app.ui.frames.ocr.frame import OcrFrame
from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.operations import operations


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
@pytest.mark.parametrize('scale', [1.0, 0.75, 0.5])
def test_modules_construct_across_language_theme_scale(ui_root, monkeypatch, language, scale):
    monkeypatch.setattr(translations, '_current_lang', language)
    for name in ('FUENTE_BASE', 'FUENTE_TITULO', 'FUENTE_CHICA'):
        monkeypatch.setattr(fonts, name, getattr(fonts, name))
    monkeypatch.setitem(ctk.ThemeManager.theme['CTkFont'], 'family', ctk.ThemeManager.theme['CTkFont']['family'])
    fonts.inicializar_fuentes(language)
    monkeypatch.setattr(OcrFrame, '_inicializar_en_background', lambda self: None)
    monkeypatch.setattr(RemoveBgFrame, '_inicializar_en_background', lambda self: self._build_content_ready(True, True))
    # Isolate the library's process-global callback registry between root fixtures.
    monkeypatch.setattr(ctk.ScalingTracker, 'window_widgets_dict', {})
    original = colors._load_theme()
    try:
        ctk.set_widget_scaling(scale)
        for theme in colors.get_theme_names():
            colors.apply_theme(theme)
            for spec in iter_all_modules():
                if not spec.enabled:
                    continue
                frame = load_frame_class(spec)(ui_root)
                frame.pack(fill='both', expand=True)
                ui_root.update_idletasks()
                ui_root.update()
                operations.drain(lambda owner: bool(owner.winfo_exists()))
                assert frame.winfo_exists()
                assert frame._title != ''
                frame.pack_forget()
                frame.pack()
                ui_root.update_idletasks()
                frame.destroy()
    finally:
        ctk.ScalingTracker.window_widgets_dict.clear()
        ctk.set_widget_scaling(1.0)
        colors.apply_theme(original)
