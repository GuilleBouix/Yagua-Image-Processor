"""Output policy: collisions, strict size protection and atomic publication."""
import shutil
from pathlib import Path

import piexif
import pytest
from PIL import Image, ImageCms

from app.modules.compress import batch_comprimir
from app.modules.convert import batch_convertir_safe
from app.modules.metadata_batch import MetadataDraft, MetadataTask, procesar_lote
from app.modules.resize import batch_canvas, batch_recortar, batch_redimensionar
from app.modules.watermark import batch_aplicar_watermark
from app.utils.saving import fingerprint, get_plan, plan_outputs, run_plan


def picture(path, fmt='PNG', *, quality=95, size=(128, 96), **kwargs):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.effect_noise(size, 70).convert('RGB').save(path, fmt, quality=quality, **kwargs)
    return str(path)


@pytest.mark.parametrize('fmt,extension', [('JPEG', '.jpeg'), ('WEBP', '.webp')])
@pytest.mark.parametrize('strip', [False, True])
@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_recompression_never_increases_size(tmp_path, fmt, extension, strip, policy):
    source = picture(tmp_path / ('foto' + extension), fmt, quality=10)
    before, stamp = Path(source).read_bytes(), fingerprint(source)
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_comprimir([source, source], str(folder), calidad=100,
                             quitar_exif=strip, output_policy=policy)
    assert result['ok'] == result['errores'] == 0
    assert result['sin_mejora'] == 1
    assert result['total_original'] == result['total_comprimido'] == len(before)
    assert result['reduccion_pct'] == 0
    assert result['exif_no_aplicado'] == int(strip)
    assert list(folder.iterdir()) == []
    assert (Path(source).read_bytes(), fingerprint(source)) == (before, stamp)
    assert result['items'][0]['ruta_salida'] is None


@pytest.mark.parametrize('equal', [False, True])
def test_candidate_equal_or_larger_is_discarded(tmp_path, monkeypatch, equal):
    from app.modules import compress
    source = picture(tmp_path / 'foto.jpg', 'JPEG', quality=20)
    data = Path(source).read_bytes()
    # Deterministic encoder returning an equal/larger valid JPEG.
    original_save = Image.Image.save
    def save(image, target, format=None, **kwargs):
        if format == 'JPEG':
            Path(target).write_bytes(data + (b'' if equal else b'larger'))
        else:
            original_save(image, target, format, **kwargs)
    monkeypatch.setattr(Image.Image, 'save', save)
    output = tmp_path / 'output.jpg'
    result = compress.comprimir_imagen(source, str(output), quitar_exif=True)
    assert result['estado'] == 'unchanged'
    assert not output.exists()
    assert Path(source).read_bytes() == data


@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_smaller_jpeg_retains_alias_and_reports_real_totals(tmp_path, policy):
    source = picture(tmp_path / 'cámara.jpeg', 'JPEG', quality=100)
    before = Path(source).stat().st_size
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_comprimir([source], str(folder), calidad=20, output_policy=policy)
    row = result['items'][0]
    target = Path(row['ruta_salida'])
    assert target == (Path(source) if policy == 'overwrite' else folder / 'cámara.jpeg')
    assert result['ok'] == 1 and result['errores'] == result['sin_mejora'] == 0
    assert target.stat().st_size == result['total_comprimido'] < before
    assert row['reemplazado'] == (policy == 'overwrite')


def test_conversion_same_format_protected_and_different_format_growth_allowed(tmp_path):
    source = picture(tmp_path / 'foto.jpg', 'JPEG', quality=10)
    before = Path(source).read_bytes()
    result = batch_convertir_safe([source], 'JPEG', tmp_path, calidad=100, output_policy='overwrite')
    assert result['sin_mejora'] == 1 and result['ok'] == 0
    result = batch_convertir_safe([source], 'BMP', tmp_path, output_policy='overwrite')
    row = result['items'][0]
    assert row['estado'] == 'saved' and row['tam_resultado'] > len(before)
    assert Path(row['ruta_salida']) == tmp_path / 'foto.bmp'
    assert Path(source).read_bytes() == before


def test_actual_format_not_extension_controls_protection(tmp_path):
    source = picture(tmp_path / 'disfraz.png', 'JPEG', quality=10)
    before = Path(source).read_bytes()
    result = batch_convertir_safe([source], 'JPEG', tmp_path, calidad=100, output_policy='overwrite')
    assert result['sin_mejora'] == 1 and result['ok'] == 0
    assert Path(source).read_bytes() == before


@pytest.mark.parametrize('processor,options', [
    (batch_redimensionar, {'porcentaje': 50}),
    (batch_recortar, {'ratio': '1:1'}),
    (batch_canvas, {'ancho': 200, 'alto': 200, 'color_fondo': (255, 255, 255)}),
])
@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_resize_outputs_no_suffixes(tmp_path, processor, options, policy):
    source = picture(tmp_path / 'foto.tif', 'TIFF')
    folder = tmp_path / 'out'
    folder.mkdir()
    result = processor([source, source], str(folder), **options, output_policy=policy)
    assert result['ok'] == 1, result
    target = Path(result['items'][0]['ruta_salida'])
    assert target.name == 'foto.tif'
    assert target.parent == (tmp_path if policy == 'overwrite' else folder)


def test_conflicts_protect_other_inputs_and_same_names(tmp_path):
    first = picture(tmp_path / 'a' / 'foto.png')
    second = picture(tmp_path / 'b' / 'foto.png')
    existing = Path(first).read_bytes()
    result = batch_redimensionar([first, second, first], str(Path(first).parent),
                                 porcentaje=50, output_policy='copies')
    assert result['ok'] == 2 and result['conflictos'] == 2
    assert [Path(row['destino']).name for row in result['items']] == ['foto_1.png', 'foto_2.png']
    assert Path(first).read_bytes() == existing


def test_converted_output_never_replaces_another_batch_input(tmp_path):
    first = picture(tmp_path / 'foto.png')
    second = picture(tmp_path / 'foto.jpg', 'JPEG', quality=10)
    before = Path(second).read_bytes()
    result = batch_convertir_safe([first, second], 'JPEG', tmp_path, calidad=100, output_policy='overwrite')
    assert Path(result['items'][0]['destino']).name == 'foto_1.jpg'
    assert result['items'][1]['estado'] == 'unchanged'
    assert Path(second).read_bytes() == before


@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_watermark_policy_and_auxiliary_resource(tmp_path, policy):
    source = picture(tmp_path / 'foto.png')
    mark = picture(tmp_path / 'marca.png', size=(20, 20))
    before = Path(mark).read_bytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_aplicar_watermark([source], mark, str(folder), output_policy=policy)
    assert result['ok'] == 1, result
    assert Path(result['items'][0]['destino']).name == 'foto.png'
    assert Path(mark).read_bytes() == before
    blocked = batch_aplicar_watermark([mark], mark, str(folder), output_policy='overwrite')
    assert blocked['errores'] == 1 and blocked['ok'] == 0
    assert Path(mark).read_bytes() == before


@pytest.mark.parametrize('clean', [False, True])
@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
@pytest.mark.parametrize('extension,fmt', [('.jpeg', 'JPEG'), ('.tif', 'TIFF')])
def test_metadata_save_preserves_unicode_pixels_and_basenames(tmp_path, clean, policy, extension, fmt):
    source = picture(tmp_path / ('niño' + extension), fmt)
    with Image.open(source) as image:
        pixels = image.tobytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    result = procesar_lote((MetadataTask(source, MetadataDraft({'Artist': 'Guille Ñ'})),),
                          clean=clean, folder=str(folder), output_policy=policy)
    assert result['ok'] == 1, result
    target = Path(result['items'][0]['destino'])
    assert target.name == Path(source).name
    if not clean:
        from app.modules.metadata import leer_campos_edicion
        assert leer_campos_edicion(str(target))['Artist'] == 'Guille Ñ'
        with Image.open(target) as image:
            assert image.tobytes() == pixels


@pytest.mark.parametrize('fault', ['encode', 'changed', 'publish', 'resource'])
def test_atomic_faults_preserve_source_and_continue(tmp_path, monkeypatch, fault):
    first = picture(tmp_path / 'first.png')
    second = picture(tmp_path / 'second.png')
    resource = picture(tmp_path / 'resource.png')
    original = Path(first).read_bytes()
    plan = plan_outputs([first, second], None, 'overwrite', resources=[resource])
    import app.utils.output as output
    replace = output.os.replace
    def publish(source, destination):
        if fault == 'publish' and Path(destination) == Path(first):
            raise PermissionError('denied')
        replace(source, destination)
    monkeypatch.setattr(output.os, 'replace', publish)
    def process(source, target):
        Image.new('RGB', (4, 4), 'red').save(target)
        if source == first:
            if fault == 'encode':
                Path(target).write_bytes(b'partial')
                raise OSError('disk full')
            if fault == 'changed':
                Path(source).write_bytes(original + b'external')
            if fault == 'resource':
                Path(resource).write_bytes(Path(resource).read_bytes() + b'external')
    result = run_plan(plan, process)
    assert result['items'][0]['estado'] == 'error'
    assert Path(first).read_bytes() == original + (b'external' if fault == 'changed' else b'')
    assert result['items'][1]['estado'] == ('error' if fault == 'resource' else 'saved')
    assert not list(tmp_path.glob('.yagua-*'))


def test_changes_after_plan_and_multipage_fail_per_file(tmp_path):
    changed = picture(tmp_path / 'changed.png')
    pages = tmp_path / 'pages.tif'
    Image.new('RGB', (8, 8)).save(pages, save_all=True, append_images=[Image.new('RGB', (8, 8))])
    good = picture(tmp_path / 'good.png')
    plan = plan_outputs([changed, pages, good], None, 'overwrite')
    Path(changed).write_bytes(Path(changed).read_bytes() + b'changed')
    result = run_plan(plan, lambda source, target: shutil.copyfile(source, target) and {})
    assert result['ok'] == 1 and result['errores'] == 2
    assert not list(tmp_path.glob('.yagua-*'))


def test_wrong_plan_format_and_resources_rejected(tmp_path):
    source = picture(tmp_path / 'source.png')
    mark = picture(tmp_path / 'mark.png')
    plan = plan_outputs([source], None, 'overwrite', resources=[mark])
    with pytest.raises(ValueError, match='invalid_output_plan'):
        get_plan(plan, [source], None)
    with pytest.raises(ValueError, match='invalid_output_plan'):
        get_plan(plan, [source], None, 'JPEG', resources=[mark])


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP', 'TIFF'])
@pytest.mark.parametrize('policy', ['copies', 'overwrite'])
def test_remove_background_policy_and_transparency(tmp_path, monkeypatch, fmt, policy):
    from app.modules import remove_bg
    source = picture(tmp_path / 'foto.png')
    original = Path(source).read_bytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    def remove(image, **kwargs):
        return Image.new('RGBA', image.size, (40, 90, 180, 0))
    monkeypatch.setattr(remove_bg, '_import_rembg', lambda: (remove, None))
    monkeypatch.setattr(remove_bg, '_get_processing_session', lambda: (object(), 'test-model', False))
    status = []
    result = remove_bg.batch_quitar_fondo([source, source], str(folder), formato_salida=fmt,
                                        status_callback=status.append, output_policy=policy)
    assert result['ok'] == 1, result
    assert result['model_used'] == 'test-model'
    assert 'analyzing_image' in status
    target = Path(result['items'][0]['destino'])
    assert target.name == {'PNG': 'foto.png', 'WEBP': 'foto.webp', 'TIFF': 'foto.tiff'}[fmt]
    assert target.parent == (tmp_path if policy == 'overwrite' else folder)
    if policy == 'copies' or fmt != 'PNG':
        assert Path(source).read_bytes() == original
    with Image.open(target) as image:
        assert image.convert('RGBA').getchannel('A').getextrema()[0] == 0


def test_hardlink_alias_is_processed_once(tmp_path):
    import os
    source = picture(tmp_path / 'foto.png')
    alias = tmp_path / 'alias.png'
    os.link(source, alias)
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_redimensionar([source, str(alias)], str(folder), porcentaje=50, output_policy='copies')
    assert result['ok'] == 1 and len(result['items']) == 1


def test_prepared_plan_keeps_partial_errors_with_hardlink_duplicates(tmp_path):
    import os
    source = picture(tmp_path / 'foto.png')
    alias = tmp_path / 'alias.png'
    os.link(source, alias)
    missing = str(tmp_path / 'missing.png')
    paths = [source, str(alias), missing, missing]
    folder = tmp_path / 'out'
    folder.mkdir()
    plan = plan_outputs(paths, folder, 'copies')
    result = batch_redimensionar(paths, str(folder), porcentaje=50, output_policy=plan)
    assert result['ok'] == result['errores'] == 1
    assert len(result['items']) == 2


def test_invalid_path_does_not_abort_other_files(tmp_path):
    source = picture(tmp_path / 'foto.png')
    plan = plan_outputs(['bad\0name.png', source], None, 'overwrite')
    result = run_plan(plan, lambda source, target: shutil.copyfile(source, target) and {})
    assert result['ok'] == result['errores'] == 1


def test_conversion_progress_includes_partial_errors(tmp_path):
    from app.modules.convert import batch_convertir
    source = picture(tmp_path / 'foto.png')
    folder = tmp_path / 'out'
    folder.mkdir()
    progress = []
    result = batch_convertir([str(tmp_path / 'missing.png'), source, source], 'JPEG', str(folder),
        output_policy='copies', progress_cb=lambda count, total: progress.append((count, total)))
    assert [row['estado'] for row in result] == ['error', 'saved']
    assert progress == [(1, 2), (2, 2)]


def test_publish_race_does_not_replace_competing_copy(tmp_path):
    source = picture(tmp_path / 'foto.png')
    folder = tmp_path / 'out'
    folder.mkdir()
    plan = plan_outputs([source], folder, 'copies')
    target = folder / 'foto.png'
    def work(source, temporary):
        shutil.copyfile(source, temporary)
        target.write_bytes(b'competing file')
    result = run_plan(plan, work)
    assert result['errores'] == 1
    assert target.read_bytes() == b'competing file'
    assert not list(folder.glob('.yagua-*'))


def test_skipped_candidate_does_not_reserve_a_copy_name(tmp_path):
    small = picture(tmp_path / 'a' / 'foto.jpg', 'JPEG', quality=5)
    large = picture(tmp_path / 'b' / 'foto.jpg', 'JPEG', quality=100)
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_comprimir([small, large], str(folder), calidad=80, output_policy='copies')
    assert result['sin_mejora'] == 1 and result['ok'] == 1
    assert Path(result['items'][1]['destino']).name == 'foto.jpg'
    assert result['conflictos'] == 0


def test_interruption_removes_stage_and_preserves_previous_success(tmp_path):
    first = picture(tmp_path / 'first.png')
    second = picture(tmp_path / 'second.png')
    before = Path(second).read_bytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    plan = plan_outputs([first, second], folder, 'copies')
    def work(source, target):
        Path(target).write_bytes(Path(source).read_bytes())
        if source == second:
            raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        run_plan(plan, work)
    assert (folder / 'first.png').exists()
    assert not (folder / 'second.png').exists()
    assert Path(second).read_bytes() == before
    assert not list(folder.glob('.yagua-*'))


def test_mixed_compression_totals_include_unchanged_and_exclude_errors(tmp_path):
    small = picture(tmp_path / 'small.webp', 'WEBP', quality=5)
    large = picture(tmp_path / 'large.jpg', 'JPEG', quality=100)
    missing = str(tmp_path / 'missing.jpg')
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_comprimir([small, large, missing, small], str(folder), calidad=80,
                             quitar_exif=True, output_policy='copies')
    assert result['ok'] == result['errores'] == result['sin_mejora'] == 1
    total = Path(small).stat().st_size + Path(large).stat().st_size
    saved = Path(result['items'][1]['destino']).stat().st_size
    assert result['total_original'] == total
    assert result['total_comprimido'] == Path(small).stat().st_size + saved
    assert result['reduccion_pct'] == round((1 - result['total_comprimido'] / total) * 100, 1)


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP'])
def test_transparency_and_profile_survive_conversion(tmp_path, fmt):
    source = tmp_path / 'source.tif'
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    Image.new('RGBA', (50, 40), (20, 80, 180, 120)).save(source, icc_profile=profile)
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_convertir_safe([str(source)], fmt, str(folder), output_policy='copies')
    assert result['ok'] == 1, result
    with Image.open(result['items'][0]['destino']) as image:
        assert image.size == (50, 40)
        assert image.convert('RGBA').getchannel('A').getextrema() == (120, 120)
        if fmt == 'WEBP':
            assert image.info['icc_profile'] == profile


def test_compression_metadata_icc_and_orientation_retained_when_requested(tmp_path):
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    exif = piexif.dump({'0th': {piexif.ImageIFD.Artist: b'Author', piexif.ImageIFD.Orientation: 6}})
    source = picture(tmp_path / 'source.jpg', 'JPEG', quality=100, exif=exif, icc_profile=profile)
    folder = tmp_path / 'out'
    folder.mkdir()
    result = batch_comprimir([source], str(folder), calidad=20, quitar_exif=False, output_policy='copies')
    assert result['ok'] == 1
    target = result['items'][0]['destino']
    with Image.open(target) as image:
        assert image.info['icc_profile'] == profile
        assert image.getexif().get(piexif.ImageIFD.Orientation, 1) == 1
        assert image.size == (96, 128)
    assert piexif.load(target)['0th'][piexif.ImageIFD.Artist] == b'Author'
