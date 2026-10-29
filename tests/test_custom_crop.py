"""Contratos del recorte exacto y sus omisiones por archivo."""
import pytest
from PIL import Image, ImageDraw, ImageChops

from app.modules.resize import recortar, batch_recortar, RATIOS
from app.modules.resize_geometry import centered_crop
from app.ui.image_cache import ReducedImageCache
from app.ui.preview import render_pixels
from app.ui.saving import summary


def test_exact_crop_matches_center_and_preview(tmp_path):
    source, target = tmp_path / 'árbol.png', tmp_path / 'salida.png'
    image = Image.new('RGBA', (101, 71), (100, 30, 20, 128))
    ImageDraw.Draw(image).rectangle((10, 15, 60, 45), fill='blue')
    image.save(source)
    result = recortar(source, target, ancho=80, alto=60)
    assert result['original'] == (101, 71)
    assert result['resultado'] == (80, 60)
    with Image.open(target) as saved:
        assert ImageChops.difference(saved, image.crop((10, 5, 90, 65))).getbbox() is None
    cache = ReducedImageCache()
    spec = dict(kind='crop', dimensions=(80, 60))
    preview, _, dims = render_pixels(cache.load(source, (1024, 1024), mode='RGBA'),
                                     (1024, 1024), spec, ('#111111', '#444444'))
    actual, _, _ = render_pixels(cache.load(target, (1024, 1024), mode='RGBA'),
                                 (1024, 1024), {}, ('#111111', '#444444'))
    assert dims == (80, 60)
    assert ImageChops.difference(preview, actual).getbbox() is None


@pytest.mark.parametrize('dimensions', [(None, 10), (10, None), (0, 10), (-1, 10),
                                        (1.5, 10), ('10', 10), (True, 10)])
def test_invalid_dimensions_do_not_touch_original(tmp_path, dimensions):
    path = tmp_path / 'original.png'
    Image.new('RGB', (100, 80), 'red').save(path)
    original = path.read_bytes()
    with pytest.raises(ValueError, match='invalid_dimensions'):
        recortar(path, path, ancho=dimensions[0], alto=dimensions[1])
    assert path.read_bytes() == original
    assert not list(tmp_path.glob('.yagua-*'))


@pytest.mark.parametrize('policy', [None, 'copies', 'overwrite'])
def test_batch_skips_small_and_continues(tmp_path, policy):
    paths = [tmp_path / 'small.png', tmp_path / 'large.png', tmp_path / 'broken.png']
    Image.new('RGB', (20, 20), 'red').save(paths[0])
    Image.new('RGB', (100, 80), 'blue').save(paths[1])
    paths[2].write_bytes(b'not an image')
    original = paths[0].read_bytes()
    result = batch_recortar(paths, tmp_path, ancho=80, alto=60, output_policy=policy)
    assert result['ok'] == 1
    assert result['omitidos'] == 1
    assert result['errores'] == 1
    assert paths[0].read_bytes() == original
    assert not (tmp_path / 'small_crop.png').exists()
    assert not (tmp_path / 'small_1.png').exists()
    assert not list(tmp_path.glob('.yagua-*'))
    if policy:
        assert result['resultados'][0]['estado'] == 'skipped'
        assert result['resultados'][0]['motivo'] == 'crop_too_large'
        assert result['sin_mejora'] == 0
        assert 'crop_too_large' not in summary(result)


def test_crop_uses_oriented_dimensions(tmp_path):
    source, target = tmp_path / 'rotada.jpg', tmp_path / 'out.jpg'
    exif = Image.Exif()
    exif[274] = 6
    Image.new('RGB', (100, 60), 'red').save(source, exif=exif)
    result = recortar(source, target, ancho=50, alto=90)
    assert result['original'] == (60, 100)
    assert result['resultado'] == (50, 90)
    with pytest.raises(ValueError, match='crop_too_large'):
        recortar(source, target, ancho=90, alto=50)


@pytest.mark.parametrize('ratio', RATIOS.values())
def test_ratio_and_exact_full_size_preserve_geometry(ratio):
    box = centered_crop((100, 80), ratio)
    assert 0 <= box[0] < box[2] <= 100
    assert 0 <= box[1] < box[3] <= 80
    assert centered_crop((100, 80), dimensions=(100, 80)) == (0, 0, 100, 80)


def test_existing_coordinate_crop_is_preserved(tmp_path):
    source, target = tmp_path / 'source.png', tmp_path / 'out.png'
    Image.new('RGB', (100, 80), 'red').save(source)
    assert recortar(source, target, izq=10, sup=15, der=60, inf=55)['resultado'] == (50, 40)


@pytest.mark.parametrize('count', [1, 100])
def test_exact_crop_real_batch_sizes(tmp_path, count):
    paths = []
    for index in range(count):
        path = tmp_path / f'foto-{index}.png'
        Image.new('RGB', (8, 6), (index, 30, 80)).save(path)
        paths.append(path)
    folder = tmp_path / 'copies'
    folder.mkdir()
    result = batch_recortar(paths, folder, ancho=4, alto=2, output_policy='copies')
    assert (result['ok'], result['errores']) == (count, 0)
    assert len(list(folder.glob('*.png'))) == count
    for index, path in enumerate(paths):
        with Image.open(folder / path.name) as output:
            assert output.size == (4, 2)
            assert output.getpixel((0, 0)) == (index, 30, 80)
