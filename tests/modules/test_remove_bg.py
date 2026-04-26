import builtins
from pathlib import Path

import pytest
from PIL import Image

from app.modules import remove_bg
from app.modules.remove_bg import (
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    _decontaminate_light_halo,
    estado_rembg,
    modelo_descargado,
    quitar_fondo,
    rembg_disponible,
)


@pytest.fixture(autouse=True)
def reset_remove_bg_state():
    remove_bg._SESSION_CACHE.clear()
    remove_bg._MODEL_READY.clear()
    yield
    remove_bg._SESSION_CACHE.clear()
    remove_bg._MODEL_READY.clear()


def test_rembg_disponible():
    if not rembg_disponible():
        pytest.skip("rembg no disponible en el entorno de test")


def test_estado_rembg_retorna_error_real(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'rembg':
            raise RuntimeError('No package metadata was found for pymatting')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    disponible, detalle = estado_rembg()

    assert disponible is False
    assert detalle == 'No package metadata was found for pymatting'


def test_quitar_fondo_usa_modelo_por_defecto_y_refinado_claro(tmp_path: Path, monkeypatch):
    entrada = tmp_path / "producto.png"
    salida_dir = tmp_path / "out"
    salida_dir.mkdir()

    img = Image.new("RGB", (24, 24), (255, 255, 255))
    for x in range(6, 18):
        for y in range(6, 18):
            img.putpixel((x, y), (180, 20, 20))
    img.save(entrada)

    llamadas = {"new_session": [], "remove": []}

    def fake_new_session(model_name):
        llamadas["new_session"].append(model_name)
        return {"model": model_name}

    def fake_remove(image, **kwargs):
        llamadas["remove"].append(kwargs)
        return image.convert("RGBA")

    monkeypatch.setattr(remove_bg, "_import_rembg", lambda: (fake_remove, fake_new_session))

    res = quitar_fondo(str(entrada), str(salida_dir))

    assert llamadas["new_session"] == [DEFAULT_MODEL]
    assert llamadas["remove"][0]["post_process_mask"] is True
    assert llamadas["remove"][0]["alpha_matting"] is True
    assert llamadas["remove"][0]["alpha_matting_foreground_threshold"] == 250
    assert llamadas["remove"][0]["alpha_matting_background_threshold"] == 15
    assert llamadas["remove"][0]["alpha_matting_erode_size"] == 5
    assert res["model_used"] == DEFAULT_MODEL
    assert res["used_fallback"] is False
    assert res["background_profile"] == "light_uniform"
    assert Path(res["ruta_salida"]).exists()


def test_quitar_fondo_cae_al_modelo_fallback(tmp_path: Path, monkeypatch):
    entrada = tmp_path / "producto.png"
    salida_dir = tmp_path / "out"
    salida_dir.mkdir()
    Image.new("RGB", (20, 20), (255, 255, 255)).save(entrada)

    def fake_new_session(model_name):
        if model_name == DEFAULT_MODEL:
            raise RuntimeError("modelo principal no disponible")
        return {"model": model_name}

    def fake_remove(image, **kwargs):
        return image.convert("RGBA")

    monkeypatch.setattr(remove_bg, "_import_rembg", lambda: (fake_remove, fake_new_session))

    res = quitar_fondo(str(entrada), str(salida_dir))

    assert res["model_used"] == FALLBACK_MODEL
    assert res["used_fallback"] is True


def test_modelo_descargado_respeta_u2net_home(tmp_path: Path, monkeypatch):
    custom_home = tmp_path / "models"
    custom_home.mkdir()
    (custom_home / f"{DEFAULT_MODEL}.onnx").write_bytes(b"fake-model")
    monkeypatch.setenv("U2NET_HOME", str(custom_home))

    assert modelo_descargado() is True


def test_decontaminate_light_halo_reduce_spill():
    img = Image.new("RGBA", (3, 3), (255, 255, 255, 0))
    img.putpixel((1, 1), (210, 20, 20, 255))
    img.putpixel((1, 0), (255, 225, 225, 120))

    refined = _decontaminate_light_halo(img, (255, 255, 255))

    assert refined.getpixel((1, 1)) == (210, 20, 20, 255)
    semi_before = img.getpixel((1, 0))
    semi_after = refined.getpixel((1, 0))
    assert semi_after[1] < semi_before[1]
    assert semi_after[2] < semi_before[2]
