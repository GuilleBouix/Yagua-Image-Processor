"""Pruebas de interfaz para palette frame y sus estados principales."""

from app.ui.frames.palette.frame import PaletteFrame


def test_palette_frame_build(ui_root):
    frame = PaletteFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_frame_preview")


def test_corrupt_selection_preserves_previous_state(ui_root, monkeypatch, tmp_path):
    frame = PaletteFrame(ui_root)
    broken = tmp_path / 'broken.png'
    broken.write_bytes(b'not an image')
    frame._state.ruta = 'previous.png'
    frame._state.paleta = [(255, 0, 0)]
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.askopenfilename', lambda **kwargs: str(broken))
    monkeypatch.setattr('app.ui.operations.Thread.start', lambda thread: thread.run())
    frame._explorar()
    from app.ui.operations import operations
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert frame._state.ruta == 'previous.png'
    assert frame._state.paleta == [(255, 0, 0)]
    assert frame._btn_guardar.cget('state') == 'normal'
