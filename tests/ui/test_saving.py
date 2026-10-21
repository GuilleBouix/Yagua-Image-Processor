"""Module save controls, cancellation, summaries and retained file rows."""
from importlib import import_module
from time import monotonic, sleep

from PIL import Image
import pytest

from app import translations
from app.translations import t
from app.ui.image_cache import image_cache
from app.ui.operations import operations
from app.ui.saving import mode, summary


MODULES = [('compress', 'CompressFrame'), ('convert', 'ConvertFrame'), ('resize', 'ResizeFrame'),
           ('watermark', 'WatermarkFrame'), ('remove_bg', 'RemoveBgFrame'), ('metadata', 'MetadataFrame')]


def pump(root, condition=lambda: False, timeout=.3):
    deadline = monotonic() + timeout
    while monotonic() < deadline and not condition():
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        root.update()
        sleep(.003)


def synchronous(view, monkeypatch):
    def submit(work, **kwargs):
        result = work()
        kwargs.get('on_success', lambda value: None)(result)
        return True
    monkeypatch.setattr(view, '_submit_job', submit)


@pytest.mark.parametrize('module,klass', MODULES)
def test_selector_default_and_cancellation(ui_root, tmp_path, monkeypatch, module, klass):
    imported = import_module(f'app.ui.frames.{module}.frame')
    if module == 'remove_bg':
        monkeypatch.setattr(imported, 'estado_rembg', lambda: (True, None))
        monkeypatch.setattr(imported, 'modelo_descargado', lambda: True)
    view = getattr(imported, klass)(ui_root)
    if module == 'remove_bg':
        pump(ui_root, lambda: hasattr(view, '_save_choice'), 5)
    synchronous(view, monkeypatch)
    assert mode(view) == 'copies'
    source = tmp_path / 'cámara.jpeg'
    Image.new('RGB', (16, 12)).save(source)
    before = source.read_bytes()
    folder = tmp_path / 'out'
    folder.mkdir()
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kw: str(folder))
    confirmations = []
    def cancel(title, text, **kwargs):
        confirmations.append(text)
        return False
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', cancel)
    for choice, target, count in [('save_copies', None, (0, 1)),
                                 ('save_overwrite', None, (1, 0)),
                                 ('save_overwrite', 'WEBP', (0, 1))]:
        view._save_choice.set(t(choice))
        view._prepare_save([str(source)], target, lambda *args: pytest.fail('Cancelled batch started'))
        message = t('save_confirm').format(replace=count[0], copies=count[1])
        if choice == 'save_overwrite' and target == 'WEBP':
            message += '\n\n' + t('save_format_hint')
        assert confirmations[-1] == message
    assert source.read_bytes() == before and not list(folder.iterdir())


def test_cancel_folder_stops_before_preflight(ui_root, monkeypatch):
    from app.ui.frames.compress.frame import CompressFrame
    view = CompressFrame(ui_root)
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kw: '')
    monkeypatch.setattr(view, '_submit_job', lambda *a, **kw: pytest.fail('No folder'))
    assert view._prepare_save([], None, lambda *args: None) is False


@pytest.mark.parametrize('module,klass', MODULES)
def test_save_groups_reuse_widgets_and_follow_image_presence(ui_root, tmp_path, monkeypatch, module, klass):
    imported = import_module(f'app.ui.frames.{module}.frame')
    if module == 'remove_bg':
        monkeypatch.setattr(imported, 'estado_rembg', lambda: (True, None))
        monkeypatch.setattr(imported, 'modelo_descargado', lambda: True)
    view = getattr(imported, klass)(ui_root)
    if module == 'remove_bg':
        pump(ui_root, lambda: hasattr(view, '_save_choice'), 5)
    groups = tuple(view._save_groups)
    assert groups and all(not group.winfo_manager() for group in groups)
    assert all(t('save_format_hint') not in [child.cget('text') for child in group.winfo_children()
               if hasattr(child, '_text')] for group in groups)
    source = tmp_path / 'foto.jpeg'
    Image.new('RGB', (20, 15)).save(source)
    if module == 'metadata':
        view._cargar_lote([str(source)])
        pump(ui_root, lambda: view._state.ruta_edicion is not None, 5)
    else:
        view._cargar_imagenes([str(source)])
    assert all(group.winfo_manager() for group in groups)
    view._save_choice.set(t('save_overwrite'))
    view._limpiar()
    assert all(not group.winfo_manager() for group in groups)
    assert tuple(view._save_groups) == groups
    assert mode(view) == 'overwrite'  # Preserve this session's choice.


def test_overwrite_refreshes_sizes_and_thumbnails_without_recreating_rows(ui_root, tmp_path, monkeypatch):
    from app.ui.frames.compress.frame import CompressFrame
    ui_root.geometry('900x600')
    ui_root.deiconify()
    view = CompressFrame(ui_root)
    view.pack(fill='both', expand=True)
    source = tmp_path / 'foto.jpeg'
    Image.effect_noise((256, 192), 70).convert('RGB').save(source, quality=100)
    view._cargar_imagenes([str(source)])
    listing = view._virtual_file_list
    key = (str(source), 0)
    pump(ui_root, lambda: key in listing.virtual.rows and listing.virtual.rows[key].photo is not None, 5)
    row = listing.virtual.rows[key]
    old_photo = row.photo
    before = source.stat().st_size
    view._save_choice.set(t('save_overwrite'))
    view._state.calidad.set(20)
    synchronous(view, monkeypatch)
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', lambda *a, **kw: True)
    invalidations = []
    original = image_cache.invalidate
    def invalidate(path):
        invalidations.append(path)
        return original(path)
    monkeypatch.setattr(image_cache, 'invalidate', invalidate)
    view._comprimir()
    pump(ui_root, lambda: listing.virtual.rows[key].photo is not old_photo, 5)
    assert source.stat().st_size < before
    assert str(source) in invalidations
    assert listing.virtual.rows[key] is row
    assert row.photo is not old_photo
    assert t('save_saved') in row.info_label.cget('text')
    assert view._last_save_result['ok'] == 1


def test_summary_reports_exact_growth_bytes_and_skipped_exif():
    result = dict(ok=1, sin_mejora=1, errores=0, exif_no_aplicado=1, resultados=[
        dict(estado='saved', tam_original=100, tam_resultado=125),
        dict(estado='unchanged', tam_original=100, tam_resultado=100)])
    text = summary(result, strip=True)
    assert '25 B' in text and '+25.0%' in text
    assert t('save_exif_skipped').format(count=1) in text


@pytest.mark.parametrize('language', translations.AVAILABLE_LANGUAGES)
def test_all_save_strings_translated_and_placeholders_match(language):
    from string import Formatter
    reference = translations.get_translations('Español')
    target = translations.get_translations(language)
    for key, value in reference.items():
        if key.startswith('save_') or key in ('invalid_output_plan', 'output_resource_conflict'):
            assert key in target
            def fields(text):
                return {name for _, name, _, _ in Formatter().parse(text) if name}
            assert fields(value) == fields(target[key])
