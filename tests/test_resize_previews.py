"""Preview geometry must agree with real saved images, including alpha and EXIF."""
from PIL import Image, ImageDraw, ImageChops
import pytest

from app.modules.resize import redimensionar, recortar, agregar_canvas
from app.modules.resize_geometry import fit_size
from app.ui.image_cache import ReducedImageCache
from app.ui.preview import render_pixels


@pytest.mark.parametrize('size', [(101, 67), (67, 101), (1, 500), (999, 1), (1, 1)])
@pytest.mark.parametrize('bounds', [(40, 30), (10, 150), (800, 800)])
def test_fit_matches_pillow_integer_rounding(size, bounds):
    source = Image.new('RGB', size)
    source.thumbnail(bounds)
    assert fit_size(size, bounds) == source.size


@pytest.mark.parametrize('spec,processor,options', [
    ({'kind': 'resize', 'options': {'porcentaje': 50}}, redimensionar, {'porcentaje': 50}),
    ({'kind': 'resize', 'options': {'ancho': 60, 'alto': 60}}, redimensionar, {'ancho': 60, 'alto': 60}),
    ({'kind': 'resize', 'options': {'ancho': 180}}, redimensionar, {'ancho': 180}),
    ({'kind': 'resize', 'options': {'ancho': 60, 'alto': 60, 'mantener_ratio': False}},
     redimensionar, {'ancho': 60, 'alto': 60, 'mantener_ratio': False}),
    ({'kind': 'crop', 'ratio': (1, 1)}, recortar, {'ratio': '1:1'}),
    ({'kind': 'canvas', 'size': (180, 140), 'background': None}, agregar_canvas,
     {'ancho_final': 180, 'alto_final': 140, 'color_fondo': None}),
    ({'kind': 'canvas', 'size': (40, 30), 'background': (255, 255, 255)}, agregar_canvas,
     {'ancho_final': 40, 'alto_final': 30}),
])
def test_preview_matches_real_output(tmp_path, spec, processor, options):
    path, output = tmp_path / 'árbol.png', tmp_path / 'out.png'
    image = Image.new('RGBA', (100, 80), (200, 0, 0, 128))
    ImageDraw.Draw(image).rectangle((10, 20, 60, 40), fill='blue')
    image.save(path)
    cache = ReducedImageCache()
    preview, _, dims = render_pixels(cache.load(path, (1024, 1024), mode='RGBA'), (1024, 1024), spec,
                                     ('#111111', '#444444'))
    processor(path, output, **options)
    actual, _, actual_dims = render_pixels(cache.load(output, (1024, 1024), mode='RGBA'), (1024, 1024), {},
                                           ('#111111', '#444444'))
    assert dims == actual_dims
    assert ImageChops.difference(preview, actual).getbbox() is None


def test_oriented_and_huge_preview_stays_bounded(tmp_path):
    path = tmp_path / 'rotada.jpg'
    image = Image.new('RGB', (2500, 1500), 'red')
    exif = Image.Exif()
    exif[274] = 6
    image.save(path, exif=exif)
    cache = ReducedImageCache()
    source = cache.load(path, (1024, 1024), mode='RGBA')
    pixels, original, dimensions = render_pixels(source, (500, 500),
        {'kind': 'canvas', 'size': (100000, 200000), 'background': (255, 255, 255)}, ('#111111', '#444444'))
    assert original == (1500, 2500)
    assert dimensions == (100000, 200000)
    assert max(pixels.size) <= 500
    assert cache.bytes <= cache.limit_bytes
