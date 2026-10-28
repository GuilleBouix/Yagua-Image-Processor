"""Pruebas de regresión del módulo de procesamiento convert."""

from pathlib import Path

import pytest
from PIL import Image, ImageCms

from app.modules.convert import batch_convertir_safe, convertir_imagen


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


@pytest.mark.parametrize('format', ['JPEG', 'WEBP'])
@pytest.mark.parametrize('mode', ['RGB', 'RGBA', 'P'])
def test_conversion_preserves_rgb_icc_before_mode_preparation(tmp_path, format, mode):
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    source = tmp_path / 'profile.png'
    image = Image.new('RGBA', (32, 24), (20, 80, 180, 120)).convert(mode)
    image.save(source, icc_profile=profile)
    original = source.read_bytes()

    result = convertir_imagen(source, format, tmp_path)

    with Image.open(result['ruta_salida']) as output:
        assert output.info['icc_profile'] == profile
        assert output.size == (32, 24)
        assert output.mode == ('RGBA' if format == 'WEBP' and mode in ('RGBA', 'P') else 'RGB')
    assert source.read_bytes() == original


@pytest.mark.parametrize('format', ['JPEG', 'WEBP'])
def test_conversion_does_not_invent_a_profile(tmp_path, format):
    source = tmp_path / 'unprofiled.png'
    Image.new('RGB', (32, 24), 'red').save(source)
    result = convertir_imagen(source, format, tmp_path)
    with Image.open(result['ruta_salida']) as output:
        assert not output.info.get('icc_profile')


@pytest.mark.parametrize('format', ['JPEG', 'WEBP'])
def test_conversion_does_not_copy_cmyk_profile_to_rgb_pixels(tmp_path, format):
    source = tmp_path / 'cmyk.tiff'
    Image.new('CMYK', (32, 24)).save(source, icc_profile=b'CMYK-profile')
    result = convertir_imagen(source, format, tmp_path)
    with Image.open(result['ruta_salida']) as output:
        assert output.mode == 'RGB'
        assert not output.info.get('icc_profile')
