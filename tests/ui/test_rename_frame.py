"""Pruebas de interfaz para rename frame y sus estados principales."""

from app.ui.frames.rename.frame import RenameFrame


def test_rename_frame_build(ui_root):
    frame = RenameFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_btn_renombrar")
    assert hasattr(frame, "_lista_preview")
