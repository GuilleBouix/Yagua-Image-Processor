from app.ui.frames.image_transform.frame import ImageTransformFrame
from app.ui.frames.base import BaseFrame


def test_image_transform_frame_build(ui_root):
    frame = ImageTransformFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_btn_aplicar")


def test_cargar_imagenes_respeta_limite_de_100(ui_root, monkeypatch):
    def registrar_rutas(self, rutas):
        self._imagenes = list(rutas)

    monkeypatch.setattr(BaseFrame, "_cargar_imagenes", registrar_rutas)
    frame = ImageTransformFrame(ui_root)

    frame._cargar_imagenes([f"imagen-{i}.png" for i in range(101)])

    assert len(frame._state.imagenes) == 100
    assert len(frame._imagenes) == 100
    assert "101" in frame._lbl_info.cget("text")

