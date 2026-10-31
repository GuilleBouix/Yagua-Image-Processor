"""PNG/WebP metadata round trips must preserve image payloads and atomic safety."""
from pathlib import Path
import struct
import zlib

import piexif
from PIL import Image, ImageCms, ImageOps
from PIL.PngImagePlugin import PngInfo
import pytest

from app.modules import metadata, metadata_batch as batch
from app.modules.metadata_containers import png_chunks, webp_chunks


def sample(path, variant, *, orientation=1):
    """Create distinct pixel encodings with color profiles and descriptive metadata."""
    image = Image.new('RGBA', (32, 24))
    image.putdata([(i % 256, (i * 7) % 256, (i * 11) % 256, i % 256) for i in range(768)])
    fmt = 'WEBP' if variant.startswith('webp') else 'PNG'
    options = {}
    if variant == 'palette':
        image = image.convert('RGB').quantize(colors=16)
        options['transparency'] = bytes(range(16))
    elif variant == '16bit':
        image = Image.frombytes('I;16', (32, 24), b''.join(struct.pack('<H', i * 71) for i in range(768)))
    if fmt == 'WEBP':
        options.update(lossless=variant == 'webp-lossless', quality=60, exact=True, xmp=b'<xmp>private</xmp>')
    else:
        info = PngInfo()
        info.add_text('Author', 'Private author')
        info.add_itxt('Comment', 'Private 日本語')
        info.add_text('Description', 'Compressed text', zip=True)
        options['pnginfo'] = info
    options['icc_profile'] = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    options['exif'] = piexif.dump({'0th': {274: orientation}, 'Exif': {}, 'GPS': {}})
    image.save(path, fmt, **options)
    return fmt


def payloads(path, fmt):
    """Read only chunks representing pixels, palette, and alpha for lossless checks."""
    return [(kind, payload) for kind, payload in (png_chunks if fmt == 'PNG' else webp_chunks)(path.read_bytes())
            if kind in (b'IDAT', b'PLTE', b'tRNS', b'VP8 ', b'VP8L', b'ALPH')]


@pytest.mark.parametrize('variant', ['rgba', 'palette', '16bit', 'webp-lossy', 'webp-lossless'])
def test_edit_and_clean_keep_compressed_pixels_and_rendering(tmp_path, variant):
    path = tmp_path / 'imagen con ñ.data'  # Actual format, never the extension, controls capabilities.
    fmt = sample(path, variant)
    before = payloads(path, fmt)
    with Image.open(path) as source:
        original = source.copy()
        icc = source.info['icc_profile']
    request, error = metadata.preparar_campos_exif({
        'Artist': 'Guille 日本語 👀', 'UserComment': 'Café\nComentario',
        'GPSLatitude': '0', 'GPSLongitude': '0', 'ExposureTime': '1/250', 'ExposureBiasValue': '0',
    })
    assert error is None
    assert metadata.editar_exif(path, path, request) == (True, None)
    assert payloads(path, fmt) == before
    data = batch.leer_archivo(str(path))
    assert data['supported'] and data['editable'] and not data['edit_error']
    assert data['values']['Artist'] == 'Guille 日本語 👀'
    assert data['metadata']['__gps_decimal__'] == '0.0,0.0'
    with Image.open(path) as output:
        assert output.info['icc_profile'] == icc
        assert output.tobytes() == original.tobytes()
        if fmt == 'PNG':
            assert output.info['Author'] == 'Private author'
            assert output.info['Comment'] == 'Private 日本語'
        else:
            assert output.info['xmp'] == b'<xmp>private</xmp>'
    metadata.limpiar_exif(path, path)
    assert payloads(path, fmt) == before
    assert metadata.leer_metadatos(path) == {}
    with Image.open(path) as output:
        output.load()
        assert output.info['icc_profile'] == icc
        assert output.tobytes() == original.tobytes()
        assert not any(key in output.info for key in ('exif', 'xmp', 'Author', 'Comment', 'Description'))


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP'])
def test_add_exif_without_previous_block(tmp_path, fmt):
    path = tmp_path / 'photo'
    Image.new('RGBA', (12, 18), (1, 20, 80, 120)).save(path, fmt)
    before = payloads(path, fmt)
    assert batch.leer_archivo(str(path))['metadata'] == {}
    assert metadata.editar_exif(path, path, {'Artist': 'Guille'}) == (True, None)
    assert payloads(path, fmt) == before
    assert metadata.leer_metadatos(path)['Autor'] == 'Guille'


@pytest.mark.parametrize('variant', ['rgba', 'palette', '16bit', 'webp-lossy', 'webp-lossless'])
@pytest.mark.parametrize('clean', [True, False])
def test_orientation_transform_preserves_display_and_color(tmp_path, variant, clean):
    path = tmp_path / 'photo'
    sample(path, variant, orientation=6)
    with Image.open(path) as source:
        expected = ImageOps.exif_transpose(source)
        icc = source.info['icc_profile']
    if clean:
        metadata.limpiar_exif(path, path)
    else:
        request, error = metadata.preparar_campos_exif({'Artist': 'Guille'}, orientation=1)
        assert not error
        assert metadata.editar_exif(path, path, request) == (True, None)
    with Image.open(path) as output:
        assert output.size == expected.size
        assert output.mode == expected.mode
        assert output.tobytes() == expected.tobytes()
        assert output.convert('RGBA').tobytes() == expected.convert('RGBA').tobytes()
        assert output.info['icc_profile'] == icc
        assert output.getexif().get(274, 1) == 1
        if clean:
            assert not output.getexif()
            assert not any(key in output.info for key in ('xmp', 'Author', 'Comment', 'Description'))


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP', 'TIFF'])
def test_animation_or_multipage_stays_intact(tmp_path, fmt):
    path = tmp_path / 'frames'
    frames = [Image.new('RGB', (20, 20), color) for color in ('red', 'blue')]
    frames[0].save(path, fmt, save_all=True, append_images=frames[1:], duration=100, loop=0)
    before = path.read_bytes()
    data = batch.leer_archivo(str(path))
    assert data['supported'] and not data['writable']
    assert data['blocked_reason'] == 'unsupported_frames'
    assert metadata.editar_exif(path, path, {'Artist': 'X'}) == (False, 'unsupported_frames')
    with pytest.raises(ValueError, match='unsupported_frames'):
        metadata.limpiar_exif(path, path)
    assert path.read_bytes() == before


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP'])
def test_damaged_container_is_never_published(tmp_path, fmt):
    path = tmp_path / 'corrupt'
    Image.new('RGB', (20, 20)).save(path, fmt)
    # Leave a decodable image but damage its framing: trailing bytes are not a chunk.
    path.write_bytes(path.read_bytes() + b'broken-container')
    before = path.read_bytes()
    assert metadata.editar_exif(path, path, {'Artist': 'X'}) == (False, 'error')
    with pytest.raises(ValueError, match='invalid_metadata_container'):
        metadata.limpiar_exif(path, path)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob('.yagua-*'))


@pytest.mark.parametrize('count', [1, 100])
@pytest.mark.parametrize('overwrite', [False, True])
def test_mixed_batch_and_exports(tmp_path, count, overwrite):
    paths = []
    formats = ['JPEG', 'TIFF', 'PNG', 'WEBP', 'BMP']
    for i in range(count):
        path = tmp_path / f'{i}.data'
        Image.new('RGB', (20, 20), 'red').save(path, formats[i % 5])
        paths.append(str(path))
    originals = [Path(path).read_bytes() for path in paths]
    folder = tmp_path / 'out'
    folder.mkdir()
    tasks = tuple(batch.MetadataTask(path, batch.MetadataDraft({'Artist': 'Café 日本語'})) for path in paths)
    result = batch.procesar_lote(tasks, overwrite=overwrite, folder=str(folder),
                                output_policy='overwrite' if overwrite else 'copies')
    assert result['ok'] == count - count // 5
    assert result['omitidos'] == count // 5
    assert result['errores'] == 0
    for i, row in enumerate(result['items']):
        if row['estado'] == 'saved':
            assert metadata.leer_metadatos(row['destino'])['Autor'] == 'Café 日本語'
        else:
            assert row['motivo'] == 'meta_format_unsupported'
        if not overwrite or row['estado'] != 'saved':
            assert Path(paths[i]).read_bytes() == originals[i]
    for fmt in ('txt', 'json'):
        entries = batch.exportar_lote(paths, str(tmp_path / ('export.' + fmt)), fmt)
        assert len(entries) == count
        assert sum(entry['error'] == 'meta_format_unsupported' for entry in entries) == count // 5


def test_png_crc_and_malformed_exif_are_detected(tmp_path):
    path = tmp_path / 'bad.png'
    Image.new('RGB', (20, 20)).save(path)
    chunks = png_chunks(path.read_bytes())
    chunks.insert(1, (b'eXIf', b'not-a-tiff'))
    data = bytearray(b'\x89PNG\r\n\x1a\n')
    for kind, payload in chunks:
        data += struct.pack('>I', len(payload)) + kind + payload
        data += struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    path.write_bytes(data)
    before = path.read_bytes()
    assert metadata.editar_exif(path, path, {'Artist': 'X'}) == (False, 'error')
    assert path.read_bytes() == before
    data[-1] ^= 1
    with pytest.raises(ValueError, match='invalid_metadata_container'):
        png_chunks(bytes(data))


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP'])
def test_write_failure_keeps_original_and_cleans_temporaries(tmp_path, monkeypatch, fmt):
    path = tmp_path / 'original'
    Image.new('RGBA', (20, 20), (40, 50, 60, 150)).save(path, fmt)
    before = path.read_bytes()
    def fail(*args, **kwargs):
        raise PermissionError('denied')
    monkeypatch.setattr(Path, 'write_bytes', fail)
    assert metadata.editar_exif(path, path, {'Artist': 'X'}) == (False, 'error')
    with pytest.raises(PermissionError):
        metadata.limpiar_exif(path, path)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob('.yagua-*'))


@pytest.mark.parametrize('policy', [None, 'copies'])
def test_clean_mixed_batch_skips_unsupported_and_continues(tmp_path, policy):
    tasks = []
    for i, fmt in enumerate(('BMP', 'PNG', 'WEBP')):
        path = tmp_path / str(i)
        Image.new('RGBA' if fmt != 'BMP' else 'RGB', (20, 20)).save(path, fmt)
        tasks.append(batch.MetadataTask(str(path)))
    folder = tmp_path / 'output'
    folder.mkdir()
    result = batch.procesar_lote(tuple(tasks), clean=True, folder=str(folder), output_policy=policy)
    assert result['ok'] == 2 and result['omitidos'] == 1 and result['errores'] == 0
    assert len(list(folder.iterdir())) == 2


@pytest.mark.parametrize('channels', [3, 4])
@pytest.mark.parametrize('clean', [True, False])
def test_color_png16_orientation_keeps_native_samples(tmp_path, channels, clean):
    import cv2
    import numpy as np
    from app.modules.metadata_containers import rewrite
    path = tmp_path / '16bit.png'
    pixels = np.arange(20 * 30 * channels, dtype=np.uint16).reshape(20, 30, channels) * 17
    ok, encoded = cv2.imencode('.png', pixels)
    assert ok
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    chunks = png_chunks(encoded.tobytes())
    chunks.insert(1, (b'iCCP', b'ICC\x00\x00' + zlib.compress(profile)))
    data = bytearray(b'\x89PNG\r\n\x1a\n')
    for kind, payload in chunks:
        data += struct.pack('>I', len(payload)) + kind + payload
        data += struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    path.write_bytes(data)
    rewrite(path, path, 'PNG', exif=piexif.dump({'0th': {274: 6}, 'Exif': {}, 'GPS': {}}))
    if clean:
        metadata.limpiar_exif(path, path)
    else:
        request, error = metadata.preparar_campos_exif({'Artist': 'Café'}, orientation=1)
        assert not error
        assert metadata.editar_exif(path, path, request) == (True, None)
    native = cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    assert native.dtype == np.uint16
    assert np.array_equal(native, np.rot90(pixels, 3))
    assert png_chunks(path.read_bytes())[0][1][8] == 16
    with Image.open(path) as output:
        assert output.getexif().get(274, 1) == 1
        assert output.info['icc_profile'] == profile
    if not clean:
        assert metadata.leer_campos_edicion(path)['Artist'] == 'Café'
