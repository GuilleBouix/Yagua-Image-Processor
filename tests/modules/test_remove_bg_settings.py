"""User settings affect pixels and real save paths without extra model sessions."""
from dataclasses import FrozenInstanceError

from PIL import Image, ImageChops
import pytest

from app.modules import remove_bg as module
from app.modules.remove_bg import RemoveBgConfig, _adjust_edge, _process_image, _decontaminate_light_halo


@pytest.fixture(autouse=True)
def clean_sessions():
    module._SESSION_CACHE.clear()
    module._MODEL_READY.clear()
    yield
    module._SESSION_CACHE.clear()
    module._MODEL_READY.clear()


@pytest.mark.parametrize('mode,light,matting,post', [
    ('auto', True, True, True), ('auto', False, False, True),
    ('on', False, True, True), ('off', True, False, False),
])
def test_edge_modes_preserve_auto_and_allow_override(mode, light, matting, post):
    calls = []
    image = Image.new('RGB', (20, 20), 'white' if light else 'black')
    def remove(source, **kwargs):
        calls.append(kwargs)
        return source.convert('RGBA')
    _process_image(image, rembg_remove=remove, session=object(),
                   config=RemoveBgConfig(refine_edges=mode))
    assert calls[0].get('alpha_matting', False) is matting
    assert calls[0]['post_process_mask'] is post


def test_halo_strength_is_monotonic_and_does_not_change_alpha():
    image = Image.new('RGBA', (4, 4), (255, 225, 225, 120))
    values = [_decontaminate_light_halo(image, (255, 255, 255), amount) for amount in (0, 40, 100)]
    assert ImageChops.difference(values[0], image).getbbox() is None
    assert values[0].getpixel((1, 1))[1] > values[1].getpixel((1, 1))[1] > values[2].getpixel((1, 1))[1]
    assert all(value.getchannel('A').tobytes() == image.getchannel('A').tobytes() for value in values)


def test_contour_expands_with_original_colors_and_contracts():
    original = Image.new('RGB', (9, 9), (255, 0, 0))
    cutout = Image.new('RGBA', (9, 9), (0, 0, 0, 0))
    for x in range(3, 6):
        for y in range(3, 6):
            cutout.putpixel((x, y), (255, 0, 0, 255))
    expanded = _adjust_edge(cutout, original, 1)
    contracted = _adjust_edge(cutout, original, -1)
    assert expanded.getchannel('A').getbbox() == (2, 2, 7, 7)
    assert expanded.getpixel((2, 2)) == (255, 0, 0, 255)
    assert contracted.getchannel('A').getbbox() == (4, 4, 5, 5)
    assert _adjust_edge(cutout, original, 0) is cutout
    assert _adjust_edge(original.convert('RGBA'), original, -1).getpixel((0, 0))[3] == 0


@pytest.mark.parametrize('policy', [None, 'copies', 'overwrite'])
def test_batch_settings_reach_all_saved_outputs(tmp_path, monkeypatch, policy):
    module._SESSION_CACHE.clear()
    sessions, calls = [], []
    def new_session(model):
        sessions.append(model)
        return object()
    def remove(source, **kwargs):
        calls.append(kwargs)
        cutout = source.convert('RGBA')
        alpha = Image.new('L', cutout.size, 0)
        alpha.paste(255, (6, 6, 12, 12))
        cutout.putalpha(alpha)
        return cutout
    monkeypatch.setattr(module, '_import_rembg', lambda: (remove, new_session))
    paths = []
    for i in range(2):
        path = tmp_path / f'árbol-{i}.png'
        Image.new('RGB', (20, 20), 'white').save(path)
        paths.append(str(path))
    output = tmp_path / 'out'
    output.mkdir()
    config = RemoveBgConfig(refine_edges='off', halo_strength=0, edge_offset=1)
    result = module.batch_quitar_fondo(paths, output, output_policy=policy, config=config)
    assert result['ok'] == 2 and result['errores'] == 0
    assert len(sessions) == 1
    assert all(call['post_process_mask'] is False for call in calls)
    for row in result['resultados']:
        with Image.open(row['ruta_salida']) as saved:
            assert saved.getpixel((0, 0))[3] == 0
            assert saved.getpixel((5, 5))[3] == 255
    with pytest.raises(FrozenInstanceError):
        config.edge_offset = 2
    module._SESSION_CACHE.clear()


@pytest.mark.parametrize('options', [dict(refine_edges='bad'), dict(halo_strength=101),
                                    dict(edge_offset=-6)])
def test_invalid_processing_settings_are_rejected(options):
    with pytest.raises(ValueError):
        RemoveBgConfig(**options)
