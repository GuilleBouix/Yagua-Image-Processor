import types
from pathlib import Path

from app.modules.vectorizar import batch_vectorizar, vectorizar


def test_vectorizar_batch(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    # Stub de vtracer para que el test sea deterministico y no dependa del binario real.
    def convert_image_to_svg_py(in_path, out_path, **kwargs):
        # vtracer no tolera backslashes en Windows; el modulo debe normalizar a "/".
        assert "\\" not in in_path
        assert "\\" not in out_path
        Path(out_path).write_text("<svg></svg>", encoding="utf-8")

    fake = types.SimpleNamespace(convert_image_to_svg_py=convert_image_to_svg_py)
    monkeypatch.setitem(__import__("sys").modules, "vtracer", fake)

    entrada = fixtures_dir / "sample.png"
    res = batch_vectorizar([str(entrada)], str(tmp_path))

    assert res["ok"] == 1
    salida = tmp_path / "sample.svg"
    assert salida.exists()
    assert "<svg" in salida.read_text(encoding="utf-8")


def test_vectorizar_input_invalido(tmp_path: Path):
    res = vectorizar("no_existe.png", str(tmp_path))
    assert res["ok"] == 0
    assert res["error"] == "Archivo no encontrado"

