"""Pruebas de regresión del módulo de procesamiento image utils."""

from pathlib import Path

import numpy as np
from PIL import Image

from app.utils.image_utils import load_cv_image_unchanged, save_cv_image


def test_open_cv_load_save_preserva_alpha_en_rutas_unicode(tmp_path: Path):
    entrada = tmp_path / "niñez ñ.png"
    salida = tmp_path / "salida ñ.png"
    Image.new("RGBA", (3, 2), (20, 40, 60, 80)).save(entrada)

    imagen = load_cv_image_unchanged(entrada)

    assert imagen is not None
    assert imagen.shape == (2, 3, 4)
    assert save_cv_image(salida, imagen)

    reabierta = load_cv_image_unchanged(salida)
    assert reabierta is not None
    assert np.array_equal(reabierta, imagen)
