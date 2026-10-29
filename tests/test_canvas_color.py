"""Composición de Canvas y destinos transparentes seguros por archivo."""
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from app.modules.resize import agregar_canvas, batch_canvas, canvas_output_format, compose_canvas
from app.ui.image_cache import ReducedImageCache
from app.ui.preview import render_pixels
from app.utils.saving import get_plan, plan_outputs


@pytest.mark.parametrize('background', [None, (255, 255, 255), (0, 0, 0), (12, 80, 192)])
@pytest.mark.parametrize('mode', ['RGBA', 'LA', 'P'])
def test_canvas_preserves_alpha_and_matches_preview(tmp_path, background, mode):
    source, target = tmp_path / 'árbol.png', tmp_path / 'out.png'
    image = Image.new('RGBA', (4, 4), (200, 100, 50, 128))
    if mode == 'LA':
        image = image.convert('LA')
    elif mode == 'P':
        image = Image.new('P', (4, 4), 0)
        image.putpalette([200, 100, 50] + [0] * 765)
        image.info['transparency'] = bytes([128] + [255] * 255)
    image.save(source)
    rgba = image.convert('RGBA')
    expected = Image.new('RGBA', (6, 6), (*background, 255) if background is not None else (0, 0, 0, 0))
    expected.alpha_composite(rgba, (1, 1))
    agregar_canvas(source, target, 6, 6, color_fondo=background)
    with Image.open(target) as output:
        assert output.size == (6, 6)
        assert output.getpixel((1, 1)) == expected.getpixel((1, 1))
        assert output.getpixel((0, 0)) == expected.getpixel((0, 0))
    cache = ReducedImageCache()
    preview, _, _ = render_pixels(cache.load(source, (1024, 1024), mode='RGBA'), (1024, 1024),
        dict(kind='canvas', size=(6, 6), background=background), ('#111111', '#444444'))
    actual, _, _ = render_pixels(cache.load(target, (1024, 1024), mode='RGBA'),
                                 (1024, 1024), {}, ('#111111', '#444444'))
    assert ImageChops.difference(preview, actual).getbbox() is None


@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_transparent_mixed_batch_keeps_formats_and_originals(tmp_path, policy):
    sources = []
    for fmt, extension in [('JPEG', 'jpeg'), ('BMP', 'bmp'), ('GIF', 'gif'),
                            ('PNG', 'png'), ('WEBP', 'webp'), ('TIFF', 'tif'), ('AVIF', 'avif')]:
        path = tmp_path / (fmt + '.' + extension)
        Image.new('RGB', (4, 4), 'red').save(path, fmt)
        sources.append(str(path))
    originals = {path: Path(path).read_bytes() for path in sources}
    folder = tmp_path / 'copies'
    folder.mkdir()
    plan = plan_outputs(sources, folder, policy, format_resolver=canvas_output_format)
    assert (plan.replacements, plan.copies) == ((0, 7) if policy == 'copies' else (4, 3))
    result = batch_canvas(sources + sources[:1], folder, ancho=8, alto=8, color_fondo=None,
                          output_policy=policy)
    assert (result['ok'], result['errores']) == (7, 0), result
    for row in result['items']:
        original_format = next(item.source_format for item in plan.items if item.source == row['ruta_entrada'])
        with Image.open(row['ruta_salida']) as output:
            assert output.format == canvas_output_format(original_format)
            assert output.size == (8, 8)
            assert output.convert('RGBA').getpixel((0, 0))[3] == 0
        if not row['reemplazado']:
            assert Path(row['ruta_entrada']).read_bytes() == originals[row['ruta_entrada']]
        if original_format in ('JPEG', 'BMP', 'GIF'):
            assert Path(row['ruta_salida']).suffix == '.png'
            assert row['reemplazado'] is False
    assert not list(tmp_path.rglob('.yagua-*'))


def test_transparent_destination_protects_other_inputs_and_conflicts(tmp_path):
    jpeg, png = tmp_path / 'foto.jpeg', tmp_path / 'foto.png'
    Image.new('RGB', (4, 4), 'red').save(jpeg)
    Image.new('RGB', (4, 4), 'blue').save(png)
    original = png.read_bytes()
    result = batch_canvas([str(jpeg), str(png)], tmp_path, ancho=8, alto=8,
                          color_fondo=None, output_policy='copies')
    assert result['ok'] == 2
    assert [Path(row['destino']).name for row in result['items']] == ['foto_1.png', 'foto_2.png']
    assert png.read_bytes() == original


def test_canvas_rejects_mismatched_plan_and_continues_after_bad_input(tmp_path):
    good, broken = tmp_path / 'foto.jpg', tmp_path / 'broken.png'
    Image.new('RGB', (4, 4), 'red').save(good)
    broken.write_bytes(b'broken')
    old_plan = plan_outputs([str(good)], None, 'overwrite')
    with pytest.raises(ValueError, match='invalid_output_plan'):
        get_plan(old_plan, [str(good)], None, format_resolver=canvas_output_format)
    result = batch_canvas([str(broken), str(good)], None, ancho=8, alto=8,
                          color_fondo=None, output_policy='overwrite')
    assert (result['ok'], result['errores']) == (1, 1)
    assert good.exists() and good.with_suffix('.png').exists()


def test_canvas_jpeg_preview_uses_transparency_and_legacy_batch_converts(tmp_path):
    source = tmp_path / 'cámara.jpeg'
    Image.new('RGB', (4, 4), 'red').save(source)
    result = batch_canvas([str(source)], tmp_path, ancho=8, alto=8, color_fondo=None)
    assert result['ok'] == 1
    target = tmp_path / 'cámara_canvas.png'
    cache = ReducedImageCache()
    preview, _, _ = render_pixels(cache.load(source, (1024, 1024), mode='RGBA'), (1024, 1024),
        dict(kind='canvas', size=(8, 8), background=None), ('#111111', '#444444'))
    actual, _, _ = render_pixels(cache.load(target, (1024, 1024), mode='RGBA'),
                                 (1024, 1024), {}, ('#111111', '#444444'))
    assert ImageChops.difference(preview, actual).getbbox() is None


@pytest.mark.parametrize('background', [(256, 0, 0), (-1, 0, 0), (0, 0), ('red', 0, 0)])
def test_invalid_canvas_color_is_rejected(background):
    with pytest.raises(ValueError, match='invalid_option'):
        compose_canvas(Image.new('RGB', (1, 1)), (2, 2), (0, 0), background)


def test_transparent_heif_preserves_alpha_and_size(tmp_path):
    from app.utils.image_utils import init_heif_support
    assert init_heif_support()
    Image.init()
    if 'HEIF' not in Image.SAVE:
        assert canvas_output_format('HEIF') == 'PNG'
        pytest.skip('El runtime HEIF instalado sólo permite decodificar; se usa PNG.')
    source = tmp_path / 'source.heic'
    Image.new('RGBA', (40, 30), (200, 40, 10, 128)).save(source, 'HEIF', quality=100)
    result = batch_canvas([str(source)], tmp_path, ancho=60, alto=50, color_fondo=None,
                          output_policy='copies')
    assert result['ok'] == 1, result
    with Image.open(result['items'][0]['destino']) as output:
        alpha = output.convert('RGBA').getchannel('A')
        assert output.format == 'HEIF'
        assert alpha.getpixel((0, 0)) == 0
        assert alpha.getpixel((30, 25)) == 128


@pytest.mark.parametrize('fmt', ['HEIF', 'AVIF'])
def test_transparent_canvas_falls_back_when_encoder_is_missing(monkeypatch, fmt):
    Image.init()
    monkeypatch.delitem(Image.SAVE, fmt, raising=False)
    assert canvas_output_format(fmt) == 'PNG'


@pytest.mark.parametrize('count', [1, 100])
@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_transparent_canvas_real_batches_preserve_pixels(tmp_path, count, policy):
    paths = []
    originals = {}
    for index in range(count):
        path = tmp_path / f'foto-{index}.png'
        Image.new('RGBA', (8, 6), (index, 30, 80, 128)).save(path)
        paths.append(path)
        originals[path] = path.read_bytes()
    folder = tmp_path / 'copies'
    folder.mkdir()
    result = batch_canvas(paths, folder, ancho=12, alto=10, color_fondo=None, output_policy=policy)
    assert (result['ok'], result['errores']) == (count, 0)
    assert len(result['items']) == count
    for index, path in enumerate(paths):
        output = folder / path.name if policy == 'copies' else path
        with Image.open(output) as img:
            assert img.size == (12, 10)
            assert img.getpixel((0, 0))[3] == 0
            assert img.getpixel((2, 2)) == (index, 30, 80, 128)
        if policy == 'copies':
            assert path.read_bytes() == originals[path]
    assert not list(tmp_path.rglob('.yagua-*'))
