from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.modules.watermark import aplicar_watermark


def _mk_png_rgb(path: Path, size: tuple[int, int], rgb: tuple[int, int, int]):
    img = Image.new("RGB", size, rgb)
    img.save(path, format="PNG")


def _mk_png_rgba(path: Path, size: tuple[int, int], rgba: tuple[int, int, int, int]):
    img = Image.new("RGBA", size, rgba)
    img.save(path, format="PNG")


def test_watermark_caso_feliz(tmp_path: Path):
    base = tmp_path / "base.png"
    wm = tmp_path / "wm.png"
    out = tmp_path / "out.png"

    # Base verde, watermark rojo con alpha (semi-transparente)
    _mk_png_rgb(base, (80, 80), (0, 255, 0))
    _mk_png_rgba(wm, (20, 20), (255, 0, 0, 128))

    res = aplicar_watermark(
        str(base),
        str(wm),
        str(out),
        posicion="top-left",
        escala=0.5,
        opacidad=1.0,
        margen=0,
    )

    assert res["ok"] is True
    assert out.exists()


def test_watermark_input_invalido(tmp_path: Path):
    wm = tmp_path / "wm.png"
    out = tmp_path / "out.png"
    _mk_png_rgba(wm, (10, 10), (255, 0, 0, 128))

    res = aplicar_watermark("nope.png", str(wm), str(out))
    assert res["ok"] is False
    assert "imagen base" in (res["error"] or "").lower()


def test_watermark_respeta_transparencia(tmp_path: Path):
    base = tmp_path / "base.png"
    wm = tmp_path / "wm.png"
    out = tmp_path / "out.png"

    _mk_png_rgb(base, (80, 80), (0, 255, 0))
    _mk_png_rgba(wm, (20, 20), (255, 0, 0, 128))

    res = aplicar_watermark(
        str(base),
        str(wm),
        str(out),
        posicion="top-left",
        escala=0.5,
        opacidad=1.0,
        margen=0,
    )
    assert res["ok"] is True

    img = cv2.imread(str(out), cv2.IMREAD_UNCHANGED)
    assert img is not None
    assert img.shape[2] in (3, 4)

    # Pixel dentro del watermark (zona top-left), en formato BGR(A).
    b, g, r = img[5, 5][:3].astype(int)

    # Mezcla esperada: verde base (0,255,0) + rojo (0,0,255) con alpha 0.5 -> (0,~128,~128)
    assert abs(b - 0) <= 3
    assert abs(g - 128) <= 3
    assert abs(r - 128) <= 3

