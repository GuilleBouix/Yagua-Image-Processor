from pathlib import Path

import pytest

import app.modules.ocr as ocr


def test_ocr_caso_feliz_sin_modelos(monkeypatch, fixtures_dir: Path):
    # Evitar inicializar EasyOCR real: stub de reader + procesar_imagen.
    monkeypatch.setattr(ocr, "get_reader", lambda idiomas: object())
    monkeypatch.setattr(ocr, "procesar_imagen", lambda ruta, reader: "texto")

    entrada = fixtures_dir / "sample.png"
    res = ocr.batch_procesar([str(entrada)], idiomas=["es", "en"])

    assert res["ok"] == 1
    assert res["errores"] == 0
    assert str(entrada) in res["textos"]
    assert res["textos"][str(entrada)] == "texto"


def test_ocr_input_invalido():
    with pytest.raises(ValueError, match="No se pudo abrir la imagen"):
        ocr.preprocesar_imagen("no_existe.png")


def test_ocr_edge_avif_omitido(monkeypatch, fixtures_dir: Path):
    monkeypatch.setattr(ocr, "_avif_supported", lambda: False)
    monkeypatch.setattr(ocr, "get_reader", lambda idiomas: object())
    monkeypatch.setattr(ocr, "procesar_imagen", lambda ruta, reader: "ok")

    entrada = fixtures_dir / "sample.png"
    res = ocr.batch_procesar(["x.avif", str(entrada)], idiomas=["es", "en"])

    assert res["avif_omitidos"] == 1
    assert res["ok"] == 1
    assert res["errores"] == 0

