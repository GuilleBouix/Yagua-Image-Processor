from pathlib import Path

from app.modules.convert import batch_convertir_safe


def test_convertir_a_png(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"

    res = batch_convertir_safe([str(entrada)], "PNG", str(tmp_path), calidad=90)

    salida = tmp_path / "sample.png"
    assert salida.exists()
    assert res["ok"] == 1


def test_convertir_ruta_unicode_y_evitar_sobrescribir(tmp_path: Path, fixtures_dir: Path):
    entrada = tmp_path / "imagen ñ.jpg"
    entrada.write_bytes((fixtures_dir / "sample.jpg").read_bytes())

    primero = batch_convertir_safe([str(entrada)], "PNG", str(tmp_path))
    segundo = batch_convertir_safe([str(entrada)], "PNG", str(tmp_path))

    assert primero["ok"] == segundo["ok"] == 1
    assert (tmp_path / "imagen ñ.png").is_file()
    assert (tmp_path / "imagen ñ_1.png").is_file()
    assert entrada.is_file()
