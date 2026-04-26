from app.ui.frames.settings.frame import SettingsFrame


def test_settings_frame_build(ui_root):
    frame = SettingsFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_selector_idioma")
    assert hasattr(frame, "_selector_tema")
    assert hasattr(frame, "_selector_escala")
