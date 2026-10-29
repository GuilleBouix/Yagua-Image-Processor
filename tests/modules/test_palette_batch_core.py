"""Batch limits, alpha semantics, cache revisions and safe palette exports."""

from pathlib import Path

import pytest
from PIL import Image

from app.modules.palette import extraer_paleta
from app.modules.palette_batch import PaletteCache, path_key, process_palettes
from app.ui.frames.palette.state import PaletteState


def image(path, color='red'):
    Image.new('RGB', (8, 8), color).save(path)
    return path


@pytest.mark.parametrize('count', [1, 100, 105])
def test_collection_limit_duplicates_and_successive_loads(tmp_path, count):
    state = PaletteState()
    paths = [tmp_path / f'{index}.png' for index in range(count)]
    midpoint = count // 2
    state.add(paths[:midpoint])
    duplicates, excluded = state.add(paths[midpoint:] + paths[:midpoint])
    assert len(state.paths) == min(count, 100)
    assert excluded == max(count - 100, 0)
    assert duplicates == midpoint
    assert state.add([tmp_path / '.' / '0.png']) == (1, 0)


def test_transparency_ignores_hidden_rgb_without_blending(tmp_path):
    source = tmp_path / 'alpha.png'
    img = Image.new('RGBA', (4, 1))
    img.putdata([(0, 255, 0, 0), (255, 0, 0, 1), (255, 0, 0, 128), (0, 0, 255, 255)])
    img.save(source)
    assert extraer_paleta(source, 4) == [(255, 0, 0), (0, 0, 255)]
    Image.new('RGBA', (5, 5), (99, 200, 100, 0)).save(source)
    with pytest.raises(ValueError, match='palette_no_visible_colors'):
        extraer_paleta(source)


def test_indexed_transparency(tmp_path):
    source = tmp_path / 'indexed.png'
    img = Image.new('P', (4, 1))
    img.putpalette([0, 255, 0, 255, 0, 0] + [0] * 762)
    img.putdata([0, 0, 0, 1])
    img.save(source, transparency=0)
    assert extraer_paleta(source) == [(255, 0, 0)]


def test_cache_reuses_count_and_invalidates_source(tmp_path, monkeypatch):
    source = image(tmp_path / 'colors.png')
    cache = PaletteCache()
    calls = []
    from app.modules import palette_batch
    original = palette_batch.extraer_paleta
    def extract(path, count):
        calls.append(count)
        return original(path, count)
    monkeypatch.setattr(palette_batch, 'extraer_paleta', extract)
    assert cache.extract(source, 6) == cache.extract(source, 6)
    cache.extract(source, 4)
    cache.extract(source, 6)
    image(source, 'blue')
    assert cache.extract(source, 6) == ((0, 0, 255),)
    assert calls == [6, 4, 6]
    assert all(key[1] == palette_batch.file_signature(source) for key in cache._entries)


def test_cache_rejects_changes_during_extraction(tmp_path, monkeypatch):
    source = image(tmp_path / 'changing.png')
    def extract(path, count):
        image(path, 'blue')
        return [(255, 0, 0)]
    monkeypatch.setattr('app.modules.palette_batch.extraer_paleta', extract)
    with pytest.raises(OSError, match='source_changed'):
        PaletteCache().extract(source, 6)


def test_exports_repeated_names_partial_errors_and_cached_results(tmp_path, monkeypatch):
    (tmp_path / 'other').mkdir()
    a = image(tmp_path / 'gato.png')
    b = image(tmp_path / 'other' / 'gato.png', 'blue')
    broken = tmp_path / 'bad.png'
    broken.write_text('broken')
    protected = image(tmp_path / 'gato_paleta.png', 'green')
    before = {path: path.read_bytes() for path in [a, b, protected]}
    cache, progress = PaletteCache(), []
    cache.extract(a, 6)
    result = process_palettes([a, a, b, broken, protected], 6, cache,
        folder=tmp_path, progress=lambda done, total: progress.append((done, total)))
    assert len(result) == 4 and sum(bool(row['error']) for row in result) == 1
    assert progress == [(index, 4) for index in range(1, 5)]
    outputs = [Path(row['output']) for row in result if row['output']]
    assert {path.name for path in outputs} == {'gato_paleta_1.png', 'gato_paleta_2.png', 'gato_paleta_paleta.png'}
    assert all(path.read_bytes() == before[path] for path in before)
    assert not list(tmp_path.glob('.yagua-*'))
    for path in outputs:
        with Image.open(path) as img:
            assert img.format == 'PNG'


def test_export_failure_continues_without_partial_output(tmp_path, monkeypatch):
    a, b = image(tmp_path / 'a.png'), image(tmp_path / 'b.png')
    from app.modules import palette_batch
    original = palette_batch.exportar_paleta_imagen
    def export(palette, target, **kwargs):
        if Path(target).name.startswith('a_'):
            raise PermissionError('denied')
        return original(palette, target, **kwargs)
    monkeypatch.setattr(palette_batch, 'exportar_paleta_imagen', export)
    results = process_palettes([a, b], 6, PaletteCache(), folder=tmp_path)
    assert results[0]['error'] == 'denied'
    assert Path(results[1]['output']).is_file()
    assert not (tmp_path / 'a_paleta.png').exists()
    assert results[1]['path'] == path_key(b)


@pytest.mark.parametrize('count', [1, 100])
def test_save_real_batch_including_transparent_and_unreadable_files(tmp_path, count):
    paths = [image(tmp_path / f'foto-{index}.png') for index in range(count)]
    empty = tmp_path / 'empty.png'
    Image.new('RGBA', (4, 4), (1, 2, 3, 0)).save(empty)
    broken = tmp_path / 'unreadable.png'
    broken.write_bytes(b'bad')
    out = tmp_path / 'palettes'
    out.mkdir()
    result = process_palettes([*paths, empty, broken], 12, PaletteCache(), folder=out)
    assert sum(bool(item['output']) for item in result) == count
    assert sum(bool(item['error']) for item in result) == 2
    assert result[-2]['error'] == 'palette_no_visible_colors'
    assert len(list(out.glob('*.png'))) == count
    assert not list(out.glob('.yagua-*'))


def test_publication_race_never_replaces_an_existing_file(tmp_path, monkeypatch):
    source = image(tmp_path / 'foto.png')
    from app.modules import palette_batch
    original = palette_batch.exportar_paleta_imagen
    calls = 0
    def export(palette, target, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            target.write_bytes(b'created by another process')
        return original(palette, target, **kwargs)
    monkeypatch.setattr(palette_batch, 'exportar_paleta_imagen', export)
    result = process_palettes([source], 6, PaletteCache(), folder=tmp_path)
    assert not result[0]['error']
    assert Path(result[0]['output']).name == 'foto_paleta_1.png'
    assert (tmp_path / 'foto_paleta.png').read_bytes() == b'created by another process'


def test_palette_cache_remains_bounded(tmp_path):
    cache = PaletteCache()
    for index in range(101):
        source = image(tmp_path / f'{index}.png')
        for count in (4, 6, 8, 10, 12):
            cache.extract(source, count)
    assert len(cache._entries) == 500
