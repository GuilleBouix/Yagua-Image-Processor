"""Pruebas de regresión para write safety y sus contratos asociados."""

import piexif
import pytest
from PIL import Image

from app.modules.metadata import editar_exif, preparar_campos_exif
from app.utils.output import atomic_destination
from app.utils.settings import load_settings, save_settings


def test_partial_write_preserves_original(tmp_path):
    path = tmp_path / 'original.jpg'
    path.write_bytes(b'original')
    with pytest.raises(OSError):
        with atomic_destination(path) as temporary:
            temporary.write_bytes(b'partial')
            raise OSError('disk full')
    assert path.read_bytes() == b'original'
    assert list(tmp_path.iterdir()) == [path]


def test_publish_does_not_overwrite_competing_output(tmp_path):
    path = tmp_path / 'output.png'
    with pytest.raises(FileExistsError):
        with atomic_destination(path, replace=False) as temporary:
            temporary.write_bytes(b'ours')
            path.write_bytes(b'other')
    assert path.read_bytes() == b'other'


@pytest.mark.parametrize('data', ['[]', 'null', '42', '"text"', '{broken'])
def test_invalid_preferences(tmp_path, data):
    path = tmp_path / 'settings.json'
    path.write_text(data)
    assert load_settings(path) == {}


def test_settings_replace_failure_preserves_original(tmp_path, monkeypatch):
    path = tmp_path / 'settings.json'
    path.write_text('{"language": "English"}')
    def fail(*args):
        raise PermissionError('denied')
    monkeypatch.setattr('app.utils.output.os.replace', fail)
    with pytest.raises(PermissionError):
        save_settings({'language': 'Deutsch'}, path)
    assert load_settings(path)['language'] == 'English'


def test_jpeg_metadata_keeps_pixels_and_profile(tmp_path):
    path = tmp_path / 'photo.jpg'
    Image.effect_noise((32, 32), 40).convert('RGB').save(path, quality=61, icc_profile=b'profile')
    with Image.open(path) as image:
        pixels = image.tobytes()
    request, error = preparar_campos_exif({'Artist': 'Author'})
    assert error is None
    assert editar_exif(str(path), str(path), request) == (True, None)
    with Image.open(path) as image:
        assert image.tobytes() == pixels
        assert image.info['icc_profile'] == b'profile'
    assert piexif.load(str(path))['0th'][piexif.ImageIFD.Artist] == b'Author'
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert editar_exif(str(path), str(path), request) == (True, None)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_multipage_edit_rejected_without_changes(tmp_path):
    path = tmp_path / 'pages.tiff'
    image = Image.new('RGB', (4, 3))
    image.save(path, save_all=True, append_images=[image])
    before = path.read_bytes()
    request, _ = preparar_campos_exif({'Artist': 'Author'})
    assert editar_exif(str(path), str(path), request) == (False, 'unsupported_frames')
    assert path.read_bytes() == before


@pytest.mark.parametrize('iso, valid', [('65535', True), ('65536', False), ('0', False)])
def test_iso_encoding_boundary(iso, valid):
    _, error = preparar_campos_exif({'ISOSpeedRatings': iso})
    assert (error is None) == valid


def test_compression_does_not_strip_exif_if_candidate_larger(tmp_path):
    from app.modules.compress import comprimir_imagen
    source = tmp_path / 'input.jpg'
    output = tmp_path / 'output.jpg'
    exif = piexif.dump({'0th': {piexif.ImageIFD.Artist: b'PRIVATE'}})
    Image.effect_noise((16, 16), 90).convert('RGB').save(source, quality=10, optimize=True, exif=exif)
    before = source.read_bytes()
    result = comprimir_imagen(str(source), str(output), calidad=100, quitar_exif=True)
    assert result['estado'] == 'unchanged' and result['exif_no_aplicado']
    assert not output.exists() and source.read_bytes() == before


def test_transparent_grayscale_uses_white_background():
    from app.utils.image_utils import ensure_rgb_for_jpeg
    assert ensure_rgb_for_jpeg(Image.new('LA', (1, 1), (0, 0))).getpixel((0, 0)) == (255, 255, 255)


def test_partial_batch_reports_path_and_reason(tmp_path):
    from app.modules.compress import batch_comprimir
    source = tmp_path / 'valid.png'
    Image.new('RGB', (3, 3), 'red').save(source)
    missing = tmp_path / 'missing.png'
    output = tmp_path / 'output'
    output.mkdir()
    result = batch_comprimir([str(missing), str(source)], str(output))
    assert result['ok'] == 0 and result['sin_mejora'] == 1 and result['errores'] == 1
    failure = result['fallos'][0]
    assert failure['ruta'] == str(missing)
    assert failure['estado'] == 'error' and failure['motivo']
    assert not (output / 'valid_comprimido.png').exists()


def test_metadata_request_is_immutable():
    from app.modules.metadata import MetadataEditRequest
    values = {'Artist': 'A'}
    request = MetadataEditRequest(values)
    values['Artist'] = 'B'
    assert request.values['Artist'] == 'A'
    with pytest.raises(TypeError):
        request.values['Artist'] = 'C'
