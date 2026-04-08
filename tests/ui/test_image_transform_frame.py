from app.ui.frames.image_transform.frame import ImageTransformFrame


def test_image_transform_frame_build(ui_root):
    frame = ImageTransformFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_aplicar")

