"""Pruebas de interfaz para palette frame y sus estados principales."""

from app.ui.frames.palette.frame import PaletteFrame


def test_palette_frame_build(ui_root):
    frame = PaletteFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_frame_preview")


def test_corrupt_selection_never_shows_previous_palette(ui_root, monkeypatch, tmp_path):
    from app.modules.palette_batch import path_key
    from tests.ui.test_live_previews import pump
    frame = PaletteFrame(ui_root)
    broken = tmp_path / 'broken.png'
    broken.write_bytes(b'not an image')
    frame._state.paleta = [(255, 0, 0)]
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.askopenfilenames',
                        lambda **kwargs: (str(broken),))
    frame._explorar()
    pump(ui_root, lambda: not frame._worker_running)
    assert frame._state.ruta == path_key(broken)
    assert frame._state.paleta == []
    assert frame._palette_empty.cget('text')
    assert frame._btn_guardar.cget('state') == 'disabled'
    assert frame._btn_guardar_todas.cget('state') == 'normal'
