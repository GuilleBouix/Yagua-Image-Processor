from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.frames.remove_bg.services import INSTALL_COMMAND


def test_remove_bg_frame_build(monkeypatch, ui_root):
    # Evitar checks pesados en background
    monkeypatch.setattr(RemoveBgFrame, "_inicializar_en_background", lambda self: self._build_content_ready(True, True))

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_procesar")


def test_remove_bg_frame_muestra_error_real_y_comando_copiable(monkeypatch, ui_root):
    monkeypatch.setattr(
        RemoveBgFrame,
        "_inicializar_en_background",
        lambda self: self._build_content_ready(False, False, "No package metadata was found for pymatting"),
    )

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_lbl_error_dependencia")
    assert frame._lbl_error_dependencia.cget("text") == "No se pudo activar Quitar Fondo."
    assert frame._lbl_error_dependencia.cget("justify") == "left"
    assert hasattr(frame, "_entry_dependencia_cmd")
    assert frame._entry_dependencia_cmd.get() == INSTALL_COMMAND
    assert frame._entry_dependencia_cmd.cget("justify") == "left"
    assert hasattr(frame, "_btn_copiar_comando")
