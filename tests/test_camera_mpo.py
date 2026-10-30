"""Camera previews are optional derivatives; real multi-image inputs stay protected."""
import base64
import io

import piexif
import pytest
from PIL import Image

from tests.mpo_helpers import camera_mpo
from app.utils.image_source import mpo_preview_count, primary_jpeg_bytes
from app.utils.output import require_single_frame
from app.utils.saving import plan_outputs
from app.modules.compress import batch_comprimir
from app.modules.convert import batch_convertir_safe
from app.modules.resize import batch_redimensionar, batch_recortar, batch_canvas
from app.modules.metadata import editar_exif, preparar_campos_exif
from app.modules.metadata_batch import leer_archivo
from app.modules.palette import extraer_paleta
from app.modules.lqip import imagen_a_base64, generar_lqip
from app.utils.image_utils import load_cv_image, load_cv_image_unchanged
from app.utils.image_utils import normalize_common


@pytest.mark.parametrize('kind', [0x010001, 0x010002])
def test_tagged_preview_uses_main_and_restores_frame(tmp_path, kind):
    source = camera_mpo(tmp_path / 'camera.JPG', preview_type=kind)
    with Image.open(source) as image:
        image.seek(1)
        assert mpo_preview_count(image) == 1
        assert image.tell() == 1
        assert normalize_common(image).size == (160, 120)
    require_single_frame(source)
    raw = primary_jpeg_bytes(source)
    with Image.open(source) as original, Image.open(io.BytesIO(raw)) as output:
        assert output.format == 'JPEG'
        assert getattr(output, 'n_frames', 1) == 1
        assert output.tobytes() == original.tobytes()
        assert output.info['exif'] == original.info['exif']


@pytest.mark.parametrize('kind', [0, 0x020001, 0x020002, 0x020003, 0xFFFFFF])
def test_real_or_unknown_mpo_stays_blocked(tmp_path, kind):
    source = camera_mpo(tmp_path / 'stereo.JPG', preview_type=kind)
    before = open(source, 'rb').read()
    with pytest.raises(ValueError, match='unsupported_frames'):
        require_single_frame(source)
    assert plan_outputs([source], tmp_path, 'overwrite').items[0].error == 'unsupported_frames'
    assert open(source, 'rb').read() == before


def test_equal_size_frame_must_not_be_silently_dropped(tmp_path):
    source = camera_mpo(tmp_path / 'camera.JPG', same_size=True)
    with pytest.raises(ValueError, match='unsupported_frames'):
        require_single_frame(source)


def test_corrupt_size_cannot_leave_hidden_preview_bytes_in_metadata_output(tmp_path):
    source = camera_mpo(tmp_path / 'bad-size.JPG', oversized_primary=True)
    with pytest.raises(ValueError, match='unsupported_frames'):
        primary_jpeg_bytes(source)
    request, _ = preparar_campos_exif({'Artist': 'Other'})
    output = tmp_path / 'edited.jpg'
    before = open(source, 'rb').read()
    assert editar_exif(source, str(output), request)[0] is False
    assert not output.exists()
    assert open(source, 'rb').read() == before


@pytest.mark.parametrize('fmt,extension', [('GIF', '.gif'), ('TIFF', '.tif'), ('PNG', '.png'), ('WEBP', '.webp')])
def test_animated_or_multipage_remains_unchanged(tmp_path, fmt, extension):
    source = tmp_path / ('frames' + extension)
    first = Image.new('RGB', (32, 24), 'red')
    first.save(source, fmt, save_all=True, append_images=[Image.new('RGB', first.size, 'blue')])
    before = source.read_bytes()
    out = tmp_path / 'out'
    out.mkdir()
    for result in (batch_convertir_safe([str(source)], 'JPEG', str(out), output_policy='copies'),
                   batch_comprimir([str(source)], str(out), output_policy='overwrite')):
        assert result['errores'] == 1
        assert result['ok'] == 0
    assert source.read_bytes() == before
    assert not list(out.iterdir())


@pytest.mark.parametrize('module', ['convert', 'compress', 'resize', 'crop', 'canvas', 'metadata_clean'])
@pytest.mark.parametrize('mode', ['copies', 'overwrite'])
def test_shared_image_writers_accept_camera_primary(tmp_path, module, mode):
    source = camera_mpo(tmp_path / 'cámara.JPG', orientation=6)
    before = open(source, 'rb').read()
    out = tmp_path / 'out'
    out.mkdir()
    if module == 'convert':
        result = batch_convertir_safe([source], 'WEBP', str(out), output_policy=mode)
    elif module == 'compress':
        result = batch_comprimir([source], str(out), calidad=60, quitar_exif=False, output_policy=mode)
    elif module == 'resize':
        result = batch_redimensionar([source], str(out), porcentaje=50, output_policy=mode)
    elif module == 'crop':
        result = batch_recortar([source], str(out), ancho=80, alto=60, output_policy=mode)
    elif module == 'canvas':
        result = batch_canvas([source], str(out), ancho=200, alto=200, color_fondo=(255, 255, 255), output_policy=mode)
    else:
        from app.modules.metadata_batch import MetadataTask, procesar_lote
        result = procesar_lote((MetadataTask(source),), clean=True, folder=str(out), output_policy=mode)
    assert result['errores'] == 0, result
    assert result['ok'] == 1, result
    row = result['resultados'][0]
    with Image.open(row['ruta_salida']) as image:
        assert image.format != 'MPO'
        assert getattr(image, 'n_frames', 1) == 1
        assert image.size == {'resize': (60, 80), 'crop': (80, 60), 'canvas': (200, 200)}.get(module, (120, 160))
    if mode == 'copies' or module == 'convert':
        assert open(source, 'rb').read() == before


def test_metadata_edit_is_lossless_and_strips_only_mpf(tmp_path):
    source = camera_mpo(tmp_path / 'camera.JPG', orientation=6)
    before = open(source, 'rb').read()
    assert leer_archivo(source)['editable']
    request, error = preparar_campos_exif({'ImageDescription': 'Gato', 'Artist': 'Guille',
                                         'Copyright': 'CAT', 'UserComment': 'Un gato mirando', 'Software': 'Yagua'})
    assert error is None
    output = tmp_path / 'edited.jpg'
    assert editar_exif(source, str(output), request) == (True, None)
    with Image.open(source) as image, Image.open(output) as edited:
        assert edited.format == 'JPEG'
        assert image.tobytes() == edited.tobytes()
        assert image.getexif()[274] == edited.getexif()[274] == 6
    assert piexif.load(str(output))['0th'][piexif.ImageIFD.ImageDescription] == b'Gato'
    assert open(source, 'rb').read() == before
    # An unchanged metadata edit must retain the whole MPO, rather than drop previews.
    stamp = output.stat().st_mtime_ns
    assert editar_exif(str(output), str(output), request) == (True, None)
    assert output.stat().st_mtime_ns == stamp


def test_extraction_and_cv_use_red_primary_not_green_preview(tmp_path):
    from app.modules.compress import estimar_tamano
    source = camera_mpo(tmp_path / 'camera.JPG', orientation=6)
    before = open(source, 'rb').read()
    assert extraer_paleta(source, 4)[0][0] > 200
    assert estimar_tamano(source, 80) > 0
    for load in (load_cv_image, load_cv_image_unchanged):
        image = load(source)
        assert image.shape[:2] == (160, 120)
        assert image[0, 0, 2] > 200
    result = imagen_a_base64(source)
    with Image.open(io.BytesIO(base64.b64decode(result['base64']))) as image:
        assert image.size == (120, 160)
    result = generar_lqip(source, ancho=12)
    with Image.open(io.BytesIO(base64.b64decode(result['base64']))) as image:
        assert image.size == (12, 16)
    assert open(source, 'rb').read() == before


def test_missing_preview_is_rejected_without_writes(tmp_path):
    from pathlib import Path
    source = Path(camera_mpo(tmp_path / 'truncated.JPG'))
    with Image.open(source) as image:
        size = image.mpinfo[0xB002][0]['Size']
    source.write_bytes(source.read_bytes()[:size])
    with pytest.raises(ValueError, match='unsupported_frames'):
        require_single_frame(source)


def test_watermark_uses_camera_primary_as_base_and_auxiliary(tmp_path):
    from app.modules.watermark import batch_aplicar_watermark
    source = camera_mpo(tmp_path / 'camera.JPG', orientation=6)
    out = tmp_path / 'out'
    out.mkdir()
    # Both source and watermark are recognized MPOs, not arbitrary two-picture MPOs.
    watermark = camera_mpo(tmp_path / 'mark.JPG')
    result = batch_aplicar_watermark([source], watermark, str(out), output_policy='copies')
    assert result['ok'] == 1, result
    with Image.open(result['resultados'][0]['ruta_salida']) as image:
        assert image.size == (120, 160)
        assert image.format == 'JPEG'


def test_mpo_notice_property_and_same_format_overwrite(tmp_path):
    source = camera_mpo(tmp_path / 'camera.JPG')
    plan = plan_outputs([source], None, 'overwrite')
    assert plan.replacements == 1
    assert plan.items[0].embedded_previews == 1
    assert plan.items[0].source_format == plan.items[0].target_format == 'JPEG'


def test_remove_bg_receives_camera_primary(tmp_path, monkeypatch):
    from app.modules import remove_bg
    source = camera_mpo(tmp_path / 'camera.JPG', orientation=6)
    seen = []
    def fake_process(image, *args, **kwargs):
        seen.append(image.size)
        return image.convert('RGBA'), remove_bg._analyze_background(image)
    monkeypatch.setattr(remove_bg, '_import_rembg', lambda: (object(), object()))
    monkeypatch.setattr(remove_bg, '_process_image', fake_process)
    monkeypatch.setattr(remove_bg, '_get_processing_session', lambda *args: (object(), 'u2netp', False))
    out = tmp_path / 'out'
    out.mkdir()
    result = remove_bg.batch_quitar_fondo([source], str(out), output_policy='copies')
    assert result['ok'] == 1, result
    assert seen == [(120, 160)]
