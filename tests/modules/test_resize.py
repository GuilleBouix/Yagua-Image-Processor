"""Pruebas de regresión del módulo de procesamiento resize."""

from pathlib import Path

from app.modules.resize import redimensionar, recortar, agregar_canvas
from tests.conftest import assert_image_size


def test_redimensionar(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.png"
    salida = tmp_path / "sample_32.png"

    redimensionar(str(entrada), str(salida), ancho=32, alto=32)
    assert salida.exists()
    assert_image_size(salida, (32, 32))


def test_recortar_ratio(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample_rect.jpg"
    salida = tmp_path / "sample_crop.jpg"

    recortar(str(entrada), str(salida), ratio="1:1")
    assert salida.exists()
    assert_image_size(salida, (80, 80))


def test_canvas(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.png"
    salida = tmp_path / "sample_canvas.png"

    agregar_canvas(str(entrada), str(salida), ancho_final=120, alto_final=120, color_fondo=(255, 255, 255))
    assert salida.exists()
    assert_image_size(salida, (120, 120))
