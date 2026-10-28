"""Pruebas de regresión del módulo de procesamiento compress."""

from pathlib import Path

from app.modules.compress import comprimir_imagen


def test_comprimir_imagen(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"
    salida = tmp_path / "sample_comprimida.jpg"

    res = comprimir_imagen(str(entrada), str(salida), calidad=80, quitar_exif=True)

    assert Path(res["ruta_salida"]).exists()
    assert res["tam_original"] > 0
    assert res["tam_comprimido"] > 0
