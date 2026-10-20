from pathlib import Path
from time import monotonic, sleep

import customtkinter as ctk
from PIL import Image
import pytest

from app.modules.metadata_batch import leer_archivo
from app.translations import t, get_translations
from app.ui import colors
from app.ui.frames.metadata.collection import decode_preview
from app.ui.frames.metadata.frame import MetadataFrame
from app.ui.frames.metadata.state import path_key
from app.ui.operations import operations


@pytest.fixture
def frame(ui_root, monkeypatch):
    view = MetadataFrame(ui_root)
    controller = view._collection
    def enqueue(kind, key):
        if kind == 'active':
            try:
                data, error = leer_archivo(key), ''
            except Exception as exc:
                data, error = None, str(exc)
            try:
                preview, preview_error = decode_preview(key), ''
            except Exception as exc:
                preview, preview_error = None, str(exc)
            controller.loaded(controller.epoch, controller.revision, key, (data, error, preview, preview_error))
    monkeypatch.setattr(controller, 'enqueue', enqueue)
    def submit(work, **kwargs):
        try:
            result = work()
        except Exception as error:
            kwargs.get('on_error', lambda exc: None)(error)
        else:
            kwargs.get('on_success', lambda value: None)(result)
        return True
    monkeypatch.setattr(view, '_submit_job', submit)
    return view


def pictures(tmp_path, n=2):
    paths = []
    for i in range(n):
        path = tmp_path / f'gato-{i}.jpg'
        Image.new('RGB', (30, 20), 'red').save(path)
        paths.append(str(path))
    return paths


def set_value(frame, field, value):
    entry = frame._campos_edit[field]
    entry.delete(0, 'end')
    entry.insert(0, value)


def test_view_no_exif_has_preview_and_correct_target(frame, tmp_path):
    path = pictures(tmp_path, 1)[0]
    frame._cargar_lote([path])
    frame.update_idletasks()
    assert frame._state.ruta == frame._state.ruta_edicion == path
    assert frame._state.metadatos == {}
    assert frame._preview_ver.source is not None
    assert frame._preview_ver.source.size == (30, 20)
    assert frame._state.current.status == 'meta_no_exif'
    assert frame._preview_ver.name.cget('text') == Path(path).name
    assert len(frame._state.items) == 1
    assert all(not files.rows for files in frame._file_views if not files.active_view)
    frame._cambiar_tab(t('view'))
    assert f'0 {t("fields_found")}' in frame._lbl_info.cget('text')


def test_marking_is_independent_of_active_image(frame, tmp_path):
    paths = pictures(tmp_path)
    frame._cargar_lote(paths)
    active = frame._state.active
    frame._collection.mark(path_key(paths[1]), False)
    assert frame._state.active == active
    assert [item.path for item in frame._state.marked] == [paths[0]]
    frame._collection.mark_all(False)
    assert not frame._state.marked and frame._state.active == active
    frame._collection.activate(path_key(paths[1]))
    assert not frame._state.marked
    for files in frame._file_views:
        if path_key(paths[1]) in files.rows:
            assert not files.rows[path_key(paths[1])][1].get()


def test_drafts_survive_selection_tabs_and_common_fields(frame, tmp_path):
    paths = pictures(tmp_path)
    frame._cargar_lote(paths)
    set_value(frame, 'Artist', 'Guille')
    set_value(frame, 'Copyright', 'Primera')
    frame._collection.activate(path_key(paths[1]))
    set_value(frame, 'Copyright', 'Segunda')
    frame._cambiar_tab(t('view'))
    frame._cambiar_tab(t('edit'))
    frame._collection.apply_fields({'Artist': 'Común'})
    assert frame._state.items[path_key(paths[0])].draft.values['Copyright'] == 'Primera'
    assert frame._state.items[path_key(paths[1])].draft.values['Copyright'] == 'Segunda'
    assert all(item.draft.values['Artist'] == 'Común' for item in frame._state.items.values())
    frame._collection.activate(path_key(paths[0]))
    assert frame._campos_edit['Copyright'].get() == 'Primera'
    assert frame._campos_edit['Artist'].get() == 'Común'
    assert frame._state.items[path_key(paths[1])].draft.values['Artist'] == 'Común'


def test_common_fields_do_not_affect_unchecked_images(frame, tmp_path):
    paths = pictures(tmp_path)
    frame._cargar_lote(paths)
    frame._collection.mark(path_key(paths[0]), False)
    frame._collection.apply_fields({'Artist': 'Guille', 'Copyright': ''})
    assert not frame._state.items[path_key(paths[0])].draft.dirty
    assert frame._state.items[path_key(paths[1])].draft.values == {'Artist': 'Guille'}


def test_clear_confirmation_cancellation_and_stale_deliveries(frame, tmp_path, monkeypatch):
    path = pictures(tmp_path, 1)[0]
    frame._cargar_lote([path])
    set_value(frame, 'Artist', 'Pending')
    monkeypatch.setattr('app.ui.frames.metadata.collection.messagebox.askyesno', lambda *a, **k: False)
    frame._limpiar()
    assert len(frame._state.items) == 1
    old_epoch, old_revision = frame._collection.epoch, frame._collection.revision
    monkeypatch.setattr('app.ui.frames.metadata.collection.messagebox.askyesno', lambda *a, **k: True)
    frame._limpiar()
    frame._collection.loaded(old_epoch, old_revision, path_key(path), (leer_archivo(path), '', decode_preview(path), ''))
    frame.update_idletasks()
    assert not frame._state.items
    assert frame._preview_ver.source is None
    assert not frame._preview_ver.image.cget('image')
    assert frame._state.ruta_edicion is None


def test_stale_selection_cannot_replace_preview_or_form(frame, tmp_path):
    a, b = pictures(tmp_path)
    frame._cargar_lote([a, b])
    old_revision = frame._collection.revision
    frame._collection.activate(path_key(b))
    frame._collection.loaded(frame._collection.epoch, old_revision, path_key(a),
                             (leer_archivo(a), '', decode_preview(a), ''))
    assert frame._state.ruta_edicion == b
    assert frame._preview_ver.name.cget('text') == Path(b).name


def test_failed_read_is_visible_and_preserves_previous_draft(frame, tmp_path):
    a = pictures(tmp_path, 1)[0]
    broken = tmp_path / 'broken.jpg'
    broken.write_bytes(b'broken')
    frame._cargar_lote([a, str(broken)])
    set_value(frame, 'Artist', 'Previous')
    frame._collection.activate(path_key(str(broken)))
    assert frame._state.items[path_key(a)].draft.values == {'Artist': 'Previous'}
    assert frame._state.current.status == 'meta_read_error'
    assert frame._state.ruta_edicion is None
    assert frame._campos_edit['Artist'].cget('state') == 'disabled'
    assert frame._scroll_meta.winfo_children()[0].cget('text') == t('meta_read_error')
    Image.new('RGB', (20, 30)).save(broken)
    frame._collection.activate(path_key(str(broken)))
    assert frame._state.ruta_edicion == str(broken)
    assert frame._preview_ver.source is not None


def test_failed_preview_does_not_hide_metadata(frame, tmp_path):
    path = pictures(tmp_path, 1)[0]
    frame._cargar_lote([path])
    data = leer_archivo(path)
    data['metadata'] = {'Autor': 'Guille'}
    frame._collection.loaded(frame._collection.epoch, frame._collection.revision, path_key(path),
                             (data, '', None, 'preview unavailable'))
    assert frame._state.metadatos == {'Autor': 'Guille'}
    assert len(frame._metadata_rows) == 1
    assert 'preview unavailable' in frame._preview_ver.image.cget('text')


def test_readonly_active_cannot_be_edited(frame, tmp_path):
    path = tmp_path / 'view-only.png'
    Image.new('RGB', (20, 30)).save(path)
    frame._cargar_lote([str(path)])
    assert frame._state.ruta_edicion is None
    assert frame._preview_ver.source is not None
    assert frame._campos_edit['Artist'].cget('state') == 'disabled'


def test_unchanged_form_does_not_open_destination(frame, tmp_path, monkeypatch):
    frame._cargar_lote(pictures(tmp_path, 1))
    monkeypatch.setattr(frame._collection, 'destination', lambda *args: pytest.fail('No write without changes'))
    frame._guardar_edicion()
    assert frame._lbl_info.cget('text') == t('no_metadata_changes')


@pytest.mark.parametrize('overwrite', [False, True])
def test_save_selected_and_copy_draft_behavior(frame, tmp_path, monkeypatch, overwrite):
    paths = pictures(tmp_path)
    frame._cargar_lote(paths)
    set_value(frame, 'Artist', 'Guille')
    frame._collection.activate(path_key(paths[1]))
    set_value(frame, 'Artist', 'Other')
    output = tmp_path / 'copies'
    output.mkdir()
    monkeypatch.setattr(frame._collection, 'destination', lambda count: (overwrite, str(output)))
    frame._collection.save(selected=True)
    assert all(item.status == ('meta_saved' if overwrite else 'meta_copied') for item in frame._state.items.values())
    assert all(item.draft.dirty != overwrite for item in frame._state.items.values())
    if not overwrite:
        set_value(frame, 'Copyright', 'Still editable')
        frame._collection.capture()
        assert frame._state.current.draft.values['Copyright'] == 'Still editable'
    else:
        assert frame._campos_edit['Artist'].get() == 'Other'


def test_cancel_destination_preserves_original_and_draft(frame, tmp_path, monkeypatch):
    path = pictures(tmp_path, 1)[0]
    frame._cargar_lote([path])
    before = Path(path).read_bytes()
    set_value(frame, 'Artist', 'Pending')
    monkeypatch.setattr(frame._collection, 'destination', lambda count: None)
    frame._guardar_edicion()
    assert Path(path).read_bytes() == before
    assert frame._state.current.draft.values == {'Artist': 'Pending'}


def test_export_failure_reports_error_preserves_existing_file(frame, tmp_path, monkeypatch):
    frame._cargar_lote(pictures(tmp_path, 1))
    output = tmp_path / 'metadata.json'
    output.write_bytes(b'previous')
    monkeypatch.setattr('app.ui.frames.metadata.collection.filedialog.asksaveasfilename', lambda **k: str(output))
    def denied(*args):
        raise PermissionError('denied')
    monkeypatch.setattr('app.utils.output.os.replace', denied)
    frame._exportar('json')
    assert output.read_bytes() == b'previous'
    assert t('error_saving') in frame._lbl_info.cget('text')


def test_all_new_translation_keys_exist_in_nine_languages():
    from app.languages import AVAILABLE_LANGUAGES
    es = get_translations('Español')
    keys = {key for key in es if key.startswith('meta_')}
    assert len(keys) >= 31
    for language in AVAILABLE_LANGUAGES:
        translated = get_translations(language)
        assert keys <= translated.keys()
        assert all(translated[key] for key in keys)


@pytest.mark.parametrize('scale', [1, .75, .5])
@pytest.mark.parametrize('geometry', [(1360, 720), (900, 600)])
def test_workspace_lists_preview_and_fields_fit(frame, ui_root, tmp_path, geometry, scale):
    width, height = geometry
    ui_root.geometry(f'{width}x{height}')
    ui_root.deiconify()
    sidebar = ctk.CTkFrame(ui_root, width=240)
    sidebar.pack(side='left', fill='y')
    sidebar.pack_propagate(False)
    frame.pack(side='left', fill='both', expand=True)
    original = colors._load_theme()
    try:
        ctk.set_widget_scaling(scale)
        frame._cargar_lote(pictures(tmp_path))
        for tab in (t('view'), t('edit'), t('clean_batch')):
            frame._cambiar_tab(tab)
            ui_root.update()
            files = frame._file_views[(t('view'), t('edit'), t('clean_batch')).index(tab)]
            assert files.winfo_width() <= frame.winfo_width()
            for row, _, thumb, info, status in files.rows.values():
                assert row.winfo_width() <= files.list.winfo_width() + 1
                for widget in (thumb, info, status):
                    assert widget.winfo_x() + widget.winfo_width() <= row.winfo_width() + 1
            preview = frame._previews[(t('view'), t('edit'), t('clean_batch')).index(tab)]
            assert preview.source is not None
            if preview.photo:
                assert preview.photo.cget('size')[0] <= preview.image.winfo_width() / scale
    finally:
        ctk.set_widget_scaling(1)
        colors.apply_theme(original)


def test_real_reader_queue_displays_active_image_and_shuts_down(ui_root, tmp_path):
    view = MetadataFrame(ui_root)
    paths = pictures(tmp_path)
    view._cargar_lote(paths)
    view._collection.activate(path_key(paths[1]))
    deadline = monotonic() + 8
    while view._preview_ver.source is None and monotonic() < deadline:
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        ui_root.update()
        sleep(.01)
    assert view._preview_ver.source is not None
    assert view._state.ruta_edicion == paths[1]
    worker = view._collection.worker
    view.destroy()
    worker.join(timeout=2)
    assert not worker.is_alive()


def test_hundred_file_rows_and_overflow_message(frame, tmp_path):
    paths = pictures(tmp_path, 103)
    frame._cargar_lote(paths)
    assert len(frame._state.items) == 100
    assert all(len(files.rows) < 20 for files in frame._file_views)
    assert '3' in frame._lbl_info.cget('text')
    assert frame._state.current.status == 'meta_no_exif'
    frame._collection.activate(path_key(paths[1]))
    notice = t('meta_added').format(added=100, excluded=3, duplicates=0)
    assert all(notice in files.count.cget('text') for files in frame._file_views)


@pytest.mark.parametrize('overwrite,confirm', [(False, True), (True, True), (True, False)])
def test_destination_dialog_default_copies_and_overwrite_confirmation(frame, ui_root, tmp_path, monkeypatch, overwrite, confirm):
    ui_root.deiconify()
    called = []
    monkeypatch.setattr('app.ui.frames.metadata.collection.filedialog.askdirectory', lambda **kwargs: str(tmp_path))
    def ask(*args, **kwargs):
        called.append(args[1])
        return confirm
    monkeypatch.setattr('app.ui.frames.metadata.collection.messagebox.askyesno', ask)
    def interact(dialog):
        try:
            dialog.update()
            radios = [w for w in dialog.winfo_children() if isinstance(w, ctk.CTkRadioButton)]
            assert radios[0].cget('variable').get() == 'copies'
            if overwrite:
                radios[1].invoke()
            next(w for group in dialog.winfo_children() for w in group.winfo_children()
                 if isinstance(w, ctk.CTkButton) and w.cget('text') == t('meta_continue')).invoke()
            if overwrite and not confirm:
                assert dialog.winfo_exists()
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
    monkeypatch.setattr(frame, 'wait_window', interact)
    result = frame._collection.destination(3)
    assert result == (None if overwrite and not confirm else (overwrite, None if overwrite else str(tmp_path)))
    assert bool(called) == overwrite
    if called:
        assert '3' in called[0]


def test_apply_dialog_can_include_existing_fields_without_saving(frame, ui_root, tmp_path, monkeypatch):
    from app.modules.metadata_batch import MetadataDraft, MetadataTask, procesar_lote
    paths = pictures(tmp_path)
    procesar_lote((MetadataTask(paths[0], MetadataDraft({'Artist': 'Guille'})),), overwrite=True)
    frame._cargar_lote(paths)
    before = [Path(path).read_bytes() for path in paths]
    ui_root.deiconify()
    def interact(dialog):
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        try:
            dialog.update()
            choice = next(w for w in descendants(dialog) if isinstance(w, ctk.CTkCheckBox) and w.cget('text') == t('artist'))
            assert choice.get() == 0  # Existing values are available, not applied implicitly.
            choice.select()
            next(w for w in descendants(dialog) if isinstance(w, ctk.CTkButton)
                 and w.cget('text') == t('apply_changes')).invoke()
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
    monkeypatch.setattr(frame, 'wait_window', interact)
    frame._collection.choose_fields()
    assert frame._state.items[path_key(paths[1])].draft.values['Artist'] == 'Guille'
    assert [Path(path).read_bytes() for path in paths] == before


def test_actual_job_freezes_controls_and_uses_snapshot(ui_root, tmp_path, monkeypatch):
    from threading import Event
    from app.ui.frames.metadata import collection
    view = MetadataFrame(ui_root)
    paths = pictures(tmp_path)
    view._cargar_lote(paths)
    deadline = monotonic() + 8
    while view._state.ruta_edicion is None and monotonic() < deadline:
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        ui_root.update()
        sleep(.01)
    set_value(view, 'Artist', 'Snapshot')
    view._collection.apply_fields({'Artist': 'Snapshot'})
    output = tmp_path / 'out'
    output.mkdir()
    monkeypatch.setattr(view._collection, 'destination', lambda count: (False, str(output)))
    release = Event()
    original = collection.procesar_lote
    def work(*args, **kwargs):
        assert release.wait(5)
        return original(*args, **kwargs)
    monkeypatch.setattr(collection, 'procesar_lote', work)
    view._collection.save(selected=True)
    try:
        assert operations.is_busy()
        assert view._campos_edit['Artist'].cget('state') == 'disabled'
        active = view._state.active
        view._collection.activate(path_key(paths[1]))
        view._limpiar()
        assert len(view._state.items) == 2 and view._state.active == active
    finally:
        release.set()
        deadline = monotonic() + 8
        while operations.is_busy() and monotonic() < deadline:
            operations.drain(lambda owner: bool(owner.winfo_exists()))
            ui_root.update()
            sleep(.01)
    assert not operations.is_busy()
    from app.modules.metadata import leer_campos_edicion
    assert all(leer_campos_edicion(str(path))['Artist'] == 'Snapshot' for path in output.glob('*.jpg'))
    assert len(list(output.glob('*.jpg'))) == 2
    view.destroy()
