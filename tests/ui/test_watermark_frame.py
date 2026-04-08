from app.ui.frames.watermark.frame import WatermarkFrame


def test_watermark_frame_build(ui_root):
    frame = WatermarkFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_wm")
    assert hasattr(frame, "_btn_aplicar")
    assert hasattr(frame, "_canvas_preview")

