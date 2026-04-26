from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.frames.remove_bg.services import INSTALL_COMMAND
from app.translations import t


def test_remove_bg_frame_build(monkeypatch, ui_root):
    # Evitar checks pesados en background
    monkeypatch.setattr(RemoveBgFrame, "_inicializar_en_background", lambda self: self._build_content_ready(True, True))

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()
    ui_root.update()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_procesar")
    assert not hasattr(frame, "_selector_modelo")


def test_remove_bg_frame_muestra_aviso_temporal_primer_uso(monkeypatch, ui_root):
    monkeypatch.setattr(RemoveBgFrame, "_inicializar_en_background", lambda self: self._build_content_ready(True, False))

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()
    ui_root.update()

    assert frame._primer_uso_notice is not None
    assert frame._primer_uso_notice.winfo_exists()

    frame._ocultar_aviso_primer_uso()

    assert frame._primer_uso_notice is None
    assert frame._primer_uso_notice_job is None


def test_remove_bg_frame_muestra_error_real_y_comando_copiable(monkeypatch, ui_root):
    monkeypatch.setattr(
        RemoveBgFrame,
        "_inicializar_en_background",
        lambda self: self._build_content_ready(False, False, "No package metadata was found for pymatting"),
    )

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()
    ui_root.update()

    assert hasattr(frame, "_lbl_error_dependencia")
    assert frame._lbl_error_dependencia.cget("text") == t("rembg_unavailable_short")
    assert frame._lbl_error_dependencia.cget("justify") == "left"
    assert hasattr(frame, "_entry_dependencia_cmd")
    assert frame._entry_dependencia_cmd.get() == INSTALL_COMMAND
    assert frame._entry_dependencia_cmd.cget("justify") == "left"
    assert hasattr(frame, "_btn_copiar_comando")


def test_remove_bg_frame_footer_avisa_fallback(monkeypatch, ui_root):
    monkeypatch.setattr(RemoveBgFrame, "_inicializar_en_background", lambda self: self._build_content_ready(True, True))

    frame = RemoveBgFrame(ui_root)
    ui_root.update_idletasks()
    ui_root.update()

    frame._finalizar(1, 0, 0, used_fallback=True, model_used="u2netp")

    assert "u2netp" in frame._lbl_info.cget("text")
    assert t("remove_bg_fallback_notice").format(model="u2netp") in frame._lbl_info.cget("text")
