"""Pruebas de interfaz para watermark frame y sus estados principales."""

from unittest.mock import Mock

import numpy as np

import app.ui.frames.watermark.frame as watermark_frame
from app.ui.frames.base import BaseFrame
from app.ui.frames.watermark.frame import WatermarkFrame


def test_watermark_frame_build(ui_root):
    frame = WatermarkFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_wm")
    assert hasattr(frame, "_btn_aplicar")
    assert hasattr(frame, "_canvas_preview")


def test_preview_images_are_loaded_asynchronously(ui_root, monkeypatch):
    frame = WatermarkFrame(ui_root)
    workers = []

    class DeferredThread:
        def __init__(self, target, args=(), daemon=None):
            self.target = target
            self.args = args
            workers.append(self)

        def start(self):
            pass

    decode = Mock(return_value=np.zeros((600, 300, 4), dtype=np.uint8))
    monkeypatch.setattr(watermark_frame.threading, "Thread", DeferredThread)
    monkeypatch.setattr(watermark_frame, "load_cv_image_unchanged", decode)

    frame._cargar_preview_base("base.png")
    frame._cargar_preview_wm("watermark.png")

    decode.assert_not_called()
    assert len(workers) == 2

    for worker in workers:
        worker.target(*worker.args)
    ui_root.update()

    assert frame._preview_base_bgra.shape[:2] == (260, 130)
    assert frame._preview_wm_bgra.shape[:2] == (260, 130)
    assert decode.call_count == 2


def test_preview_discards_stale_result_and_uses_latest_slider_values(ui_root, monkeypatch):
    frame = WatermarkFrame(ui_root)
    frame._preview_base_bgra = np.zeros((20, 20, 4), dtype=np.uint8)
    frame._preview_wm_bgra = np.zeros((5, 5, 4), dtype=np.uint8)
    frame._preview_revision = 1
    workers = []

    class DeferredThread:
        def __init__(self, target, args=(), daemon=None):
            self.target = target
            self.args = args
            workers.append(self)

        def start(self):
            pass

    monkeypatch.setattr(watermark_frame.threading, "Thread", DeferredThread)
    monkeypatch.setattr(frame, "after", Mock(return_value="pending-preview"))
    monkeypatch.setattr(frame, "_mostrar_canvas", Mock())

    frame._lanzar_hilo_preview()
    stale_revision = workers[0].args[0]
    frame._state.escala.set(70)
    frame._disparar_preview()
    frame._lanzar_hilo_preview()  # Debounce fired while the old preview is active.

    stale_result = np.ones((20, 20, 4), dtype=np.uint8)
    frame._actualizar_preview(stale_revision, stale_result)
    frame.after.call_args.args[1]()  # Launch the deferred latest preview.

    assert len(workers) == 2
    latest_revision, _, _, _, latest_scale = workers[1].args[:5]
    assert latest_revision == frame._preview_revision
    assert latest_scale == 0.7
    frame._mostrar_canvas.assert_not_called()

    latest_result = np.full((20, 20, 4), 2, dtype=np.uint8)
    frame._actualizar_preview(latest_revision, latest_result)

    frame._mostrar_canvas.assert_called_once_with(frame._canvas_preview, latest_result)


def test_unreadable_preview_image_is_handled(ui_root, monkeypatch):
    frame = WatermarkFrame(ui_root)
    monkeypatch.setattr(
        watermark_frame,
        "load_cv_image_unchanged",
        Mock(side_effect=OSError("invalid image")),
    )
    monkeypatch.setattr(frame, "after", lambda delay, callback: callback())
    frame._preview_load_revisions["base"] = 1

    frame._cargar_preview_en_background("base", "invalid.png", 1)

    assert frame._preview_base_bgra is None
    assert frame._lbl_preview_status.cget("text") == ""


def test_empty_image_selection_clears_pending_base_preview(ui_root, monkeypatch):
    frame = WatermarkFrame(ui_root)
    frame._preview_base_bgra = np.zeros((10, 10, 4), dtype=np.uint8)
    frame._preview_load_revisions["base"] = 1
    monkeypatch.setattr(BaseFrame, "_cargar_imagenes", lambda self, rutas: None)

    frame._cargar_imagenes([])

    assert frame._preview_base_bgra is None
    assert frame._preview_load_revisions["base"] == 2
    assert frame._canvas_preview.cget("text")

