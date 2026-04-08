import builtins

import pytest

from app.modules.remove_bg import estado_rembg, rembg_disponible


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
