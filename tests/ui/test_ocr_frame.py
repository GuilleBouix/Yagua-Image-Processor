from app.ui.frames.ocr.frame import OcrFrame


def test_ocr_frame_build(monkeypatch, ui_root):
    # Evitar inicializacion pesada (EasyOCR) en background
    monkeypatch.setattr(OcrFrame, "_inicializar_en_background", lambda self: None)

    frame = OcrFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_dropdown_idiomas")
    assert hasattr(frame, "_btn_procesar")
    assert hasattr(frame, "_textarea")

    frame._textarea.insert("0.0", "hola")
    frame._limpiar()
    ui_root.update_idletasks()
    assert frame._textarea.get("0.0", "end").strip() == ""
