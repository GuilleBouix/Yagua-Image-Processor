from unittest.mock import Mock

from app.ui.frames.base import BaseFrame
from app.ui.frames.compress.frame import CompressFrame


def test_compress_frame_build(ui_root):
    frame = CompressFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_panel_opciones")
    assert hasattr(frame, "_btn_comprimir")


def test_compress_quality_slider_does_not_estimate(ui_root, monkeypatch):
    frame = CompressFrame(ui_root)
    frame._imagenes = [f"heavy-image-{index}.jpg" for index in range(100)]
    frame._lbl_info.configure(text="100 images loaded")
    estimate = Mock(side_effect=AssertionError("estimate should not run from slider"))
    monkeypatch.setattr("app.ui.frames.compress.services.estimar_tamano", estimate)

    frame._actualizar_calidad(90)

    assert frame._lbl_calidad.cget("text") == "90"
    assert frame._lbl_info.cget("text") == "100 images loaded"
    estimate.assert_not_called()


def test_compress_loading_shows_count_without_estimating(ui_root, monkeypatch):
    frame = CompressFrame(ui_root)
    monkeypatch.setattr(BaseFrame, "_cargar_imagenes", lambda self, rutas: None)
    estimate = Mock(side_effect=AssertionError("estimate should not run while loading"))
    monkeypatch.setattr("app.ui.frames.compress.services.estimar_tamano", estimate)

    frame._cargar_imagenes(["one.jpg", "two.jpg"])

    assert frame._lbl_info.cget("text").startswith("2 ")
    assert frame._state.imagenes == ["one.jpg", "two.jpg"]
    estimate.assert_not_called()


def test_compress_process_uses_selected_quality(ui_root, monkeypatch):
    frame = CompressFrame(ui_root)
    frame._imagenes = ["sample.jpg"]
    frame._state.calidad.set(83)
    batch = Mock(return_value={
        "ok": 1,
        "total_original": 100,
        "total_comprimido": 50,
        "reduccion_pct": 50.0,
        "errores": 0,
        "conflictos": 0,
    })
    monkeypatch.setattr("app.ui.frames.compress.frame.batch_comprimir", batch)
    frame._finalizar = Mock()
    monkeypatch.setattr(frame, "after", lambda delay, callback: callback())

    frame._proceso("output")

    batch.assert_called_once_with(
        ["sample.jpg"], "output", calidad=83, quitar_exif=True
    )
    frame._finalizar.assert_called_once_with(1, 100, 50, 50.0, 0, 0)
