from app.ui.frames.ocr.frame import OcrFrame
from app.ui.frames.ocr import frame as ocr_frame_module


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


def test_error_en_background_se_muestra_despues_del_except(monkeypatch):
    callbacks = []
    errors = []

    def fail_batch(*args):
        raise RuntimeError("fallo OCR de prueba")

    class FakeFrame:
        _imagenes = ["entrada.png"]

        def _post_ui(self, delay, callback):
            callbacks.append(callback)

        def _handle_error(self, message):
            errors.append(message)

    monkeypatch.setattr(ocr_frame_module, "batch_procesar", fail_batch)

    OcrFrame._proceso_ocr(FakeFrame(), ["es"])
    callbacks[0]()

    assert errors == ["fallo OCR de prueba"]
