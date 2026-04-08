from pathlib import Path

import pytest
from PIL import Image

from app.modules.image_transform import batch_transformar, transformar_imagen


def test_image_transform_caso_feliz(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.png"
    opciones = {
        "corregir_exif": False,
        "angulo_libre": 45,
        "flip_horizontal": True,
    }

    res = batch_transformar([str(entrada)], str(tmp_path), opciones)
    assert res["ok"] == 1

    salida = tmp_path / "sample_transform.png"
    assert salida.exists()
    with Image.open(salida) as img:
        # Por expand=True en rotacion libre, suele crecer respecto al original 64x64.
        assert img.size[0] > 64 or img.size[1] > 64


def test_image_transform_input_invalido(tmp_path: Path):
    opciones = {"corregir_exif": False}
    with pytest.raises(FileNotFoundError):
        transformar_imagen("nope.png", str(tmp_path / "out.png"), opciones)


def test_image_transform_jpeg_sin_alpha(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"
    opciones = {"flip_vertical": True, "corregir_exif": False}

    res = batch_transformar([str(entrada)], str(tmp_path), opciones)
    assert res["ok"] == 1

    salida = tmp_path / "sample_transform.jpg"
    assert salida.exists()
    with Image.open(salida) as img:
        assert img.mode == "RGB"

