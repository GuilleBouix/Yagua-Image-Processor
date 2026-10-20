import json
from pathlib import Path

from PIL import Image
import pytest

from app.modules import metadata_batch as batch
from app.modules.metadata import leer_campos_edicion, leer_metadatos
from app.ui.frames.metadata.state import MetadataState, path_key


def image(path, fmt='JPEG'):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (30, 20), 'red').save(path, fmt)
    return str(path)


@pytest.mark.parametrize('count', [1, 100, 103])
def test_collection_limit_and_duplicate_paths(tmp_path, count):
    state = MetadataState()
    paths = [str(tmp_path / f'{i}.jpg') for i in range(count)]
    added, excluded, duplicates = state.add(paths + paths)
    assert len(added) == min(count, 100)
    assert excluded == max(0, count - 100)
    assert duplicates == count
    assert len(state.marked) == min(count, 100)
    assert len(state.items) <= 100


def test_successive_additions_keep_selection_and_drafts(tmp_path):
    state = MetadataState()
    paths = [str(tmp_path / f'{i}.jpg') for i in range(106)]
    state.add(paths[:98])
    first = path_key(paths[0])
    state.active = first
    state.items[first].draft.values['Artist'] = 'Guille'
    assert state.add(paths[97:]) == ([path_key(p) for p in paths[98:100]], 6, 1)
    assert state.active == first
    assert state.current.draft.values == {'Artist': 'Guille'}


def test_read_error_is_not_no_exif(tmp_path):
    path = image(tmp_path / 'noexif.jpg')
    assert batch.leer_archivo(path)['metadata'] == {}
    broken = tmp_path / 'broken.jpg'
    broken.write_bytes(b'broken')
    with pytest.raises(Exception):
        batch.leer_archivo(str(broken))


@pytest.mark.parametrize('overwrite', [False, True])
@pytest.mark.parametrize('fmt,extension', [('JPEG', 'jpg'), ('TIFF', 'tiff')])
def test_unicode_individual_drafts_copy_and_overwrite(tmp_path, overwrite, fmt, extension):
    paths = [image(tmp_path / str(i) / ('same.' + extension), fmt) for i in range(2)]
    before = [Path(p).read_bytes() for p in paths]
    folder = tmp_path / 'out'
    folder.mkdir()
    tasks = tuple(batch.MetadataTask(p, batch.MetadataDraft({'Artist': f'Guille {i} 日本語 👀'}))
                  for i, p in enumerate(paths))
    result = batch.procesar_lote(tasks, overwrite=overwrite, folder=str(folder))
    assert result['ok'] == 2 and result['errores'] == 0
    outputs = [r['destino'] for r in result['items']]
    assert len(set(outputs)) == 2
    for i, output in enumerate(outputs):
        assert leer_campos_edicion(output)['Artist'] == f'Guille {i} 日本語 👀'
        if not overwrite:
            assert Path(paths[i]).read_bytes() == before[i]
        with Image.open(output) as loaded:
            assert loaded.size == (30, 20)


def test_partial_errors_unsupported_and_unchanged(tmp_path):
    good = image(tmp_path / 'good.jpg')
    invalid = image(tmp_path / 'invalid.jpg')
    unchanged = image(tmp_path / 'unchanged.jpg')
    readonly = image(tmp_path / 'read-only.png', 'PNG')
    missing = str(tmp_path / 'missing.jpg')
    tasks = (batch.MetadataTask(good, batch.MetadataDraft({'Artist': 'Guille'})),
             batch.MetadataTask(invalid, batch.MetadataDraft({'FNumber': 'nan'})),
             batch.MetadataTask(unchanged), batch.MetadataTask(readonly, batch.MetadataDraft({'Artist': 'X'})),
             batch.MetadataTask(missing, batch.MetadataDraft({'Artist': 'X'})))
    before = Path(invalid).read_bytes()
    result = batch.procesar_lote(tasks, overwrite=True)
    assert (result['ok'], result['unchanged'], result['errores']) == (1, 1, 3)
    assert [r['ruta'] for r in result['items']] == [t.path for t in tasks]
    assert Path(invalid).read_bytes() == before
    assert result['items'][3]['estado'] == 'unsupported'


def test_reread_detects_source_change_and_keeps_original(tmp_path):
    path = image(tmp_path / 'changed.jpg')
    stamp = batch.fingerprint(path)
    Path(path).write_bytes(Path(path).read_bytes() + b'changed')
    before = Path(path).read_bytes()
    result = batch.procesar_lote((batch.MetadataTask(path, batch.MetadataDraft({'Artist': 'X'}), stamp),), overwrite=True)
    assert result['items'][0]['error'] == 'source_changed'
    assert Path(path).read_bytes() == before


@pytest.mark.parametrize('overwrite', [False, True])
def test_clean_and_multipage_rejection(tmp_path, overwrite):
    path = image(tmp_path / 'gato.jpg')
    batch.procesar_lote((batch.MetadataTask(path, batch.MetadataDraft({'Artist': 'Guille'})),), overwrite=True)
    pages = tmp_path / 'pages.tiff'
    sample = Image.new('RGB', (4, 3))
    sample.save(pages, save_all=True, append_images=[sample])
    before = pages.read_bytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch.procesar_lote((batch.MetadataTask(path), batch.MetadataTask(str(pages))),
                                clean=True, overwrite=overwrite, folder=str(folder))
    assert result['ok'] == result['errores'] == 1
    assert leer_metadatos(result['items'][0]['destino']) == {}
    assert result['items'][1]['error'] == 'unsupported_frames'
    assert pages.read_bytes() == before


@pytest.mark.parametrize('fmt', ['txt', 'json'])
def test_export_same_names_no_exif_and_errors(tmp_path, fmt):
    paths = tuple(image(tmp_path / str(i) / 'gato.jpg') for i in range(2))
    batch.procesar_lote((batch.MetadataTask(paths[0], batch.MetadataDraft({'Artist': 'Guille 日本語'})),), overwrite=True)
    missing = str(tmp_path / 'missing.jpg')
    output = tmp_path / ('metadata.' + fmt)
    entries = batch.exportar_lote((*paths, missing), str(output), fmt)
    assert len(entries) == 3 and entries[0]['ruta'] != entries[1]['ruta']
    assert entries[1]['metadatos'] == {} and entries[1]['error'] is None
    assert entries[2]['error'] and not entries[2]['metadatos']
    text = output.read_text(encoding='utf-8')
    assert 'Guille 日本語' in text
    assert '__gps_decimal__' not in text
    if fmt == 'json':
        assert json.loads(text) == entries


def test_atomic_failure_does_not_replace_original(tmp_path, monkeypatch):
    path = image(tmp_path / 'original.jpg')
    before = Path(path).read_bytes()
    def denied(*args):
        raise PermissionError('denied')
    monkeypatch.setattr('app.utils.output.os.replace', denied)
    result = batch.procesar_lote((batch.MetadataTask(path, batch.MetadataDraft({'Artist': 'X'})),), overwrite=True)
    assert result['errores'] == 1
    assert Path(path).read_bytes() == before
    assert not list(tmp_path.glob('.yagua-*'))


def test_gps_and_dates_use_each_destination_baseline():
    draft = batch.MetadataDraft({'GPSLatitude': '0', 'Artist': ''}, sync_dates=True)
    request, error = batch.preparar_borrador({'GPSLongitude': '0', 'DateTimeOriginal': '2026:10:19 12:30:00'}, draft)
    assert error is None
    assert request.values['GPSLatitude'] == request.values['GPSLongitude'] == '0'
    assert request.values['DateTimeOriginal'] == '2026:10:19 12:30:00'
    assert 'Artist' not in request.values
    assert batch.preparar_borrador({}, draft)[1] == 'gps_pair'


def test_cancelled_destination_required_and_frozen_draft(tmp_path):
    path = image(tmp_path / 'original.jpg')
    draft = batch.MetadataDraft({'Artist': 'Before'})
    task = batch.MetadataTask(path, draft.copy())
    draft.values['Artist'] = 'After'
    with pytest.raises(ValueError, match='output_folder_required'):
        batch.procesar_lote((task,))
    batch.procesar_lote((task,), overwrite=True)
    assert leer_campos_edicion(path)['Artist'] == 'Before'


@pytest.mark.parametrize('count', [1, 100])
def test_full_batch_copy_and_export_keeps_every_source_identity(tmp_path, count):
    paths = tuple(image(tmp_path / str(i) / 'same.jpg') for i in range(count))
    tasks = tuple(batch.MetadataTask(path, batch.MetadataDraft({'Artist': f'Autor {i}'}))
                  for i, path in enumerate(paths))
    output = tmp_path / 'copies'
    output.mkdir()
    result = batch.procesar_lote(tasks, folder=str(output))
    assert result['ok'] == count and result['errores'] == 0
    destinations = tuple(item['destino'] for item in result['items'])
    assert len(set(destinations)) == count
    exported = batch.exportar_lote(destinations, str(tmp_path / 'all.json'), 'json')
    assert [item['metadatos']['Autor'] for item in exported] == [f'Autor {i}' for i in range(count)]
    assert all(not leer_metadatos(path) for path in paths)
