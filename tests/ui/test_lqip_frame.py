"""Pruebas de interfaz para lqip frame y sus estados principales."""

from app.ui.frames.lqip.frame import LqipFrame
from app.ui.frames.lqip import frame as frame_module
from app.ui.frames.lqip.services import ItemResult, cargar_original, procesar_archivos
from app.translations import t
from app import translations
import pytest
import customtkinter as ctk
from types import SimpleNamespace
from app.modules.lqip import _construir_resultado


def test_lqip_frame_build(ui_root):
    frame = LqipFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert not hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_lbl_input_name")
    assert hasattr(frame, "_seg_modo")
    assert hasattr(frame, "_btn_procesar")
    assert frame._modo_visible.get() == t('lqip_mode_lqip')
    assert frame._btn_copiar.cget('state') == 'disabled'
    frame.destroy()


def loaded_frame(ui_root, fixtures_dir):
    frame = LqipFrame(ui_root)
    paths = [str(fixtures_dir / 'sample.png')]
    frame._cargar_imagenes(paths)
    items = procesar_archivos(tuple(paths), frame._state.obtener_opciones())
    frame._finalizar(frame._revision, items)
    return frame


def test_format_updates_single_image_code_and_copy(ui_root, fixtures_dir):
    frame = loaded_frame(ui_root, fixtures_dir)
    assert frame._selected_index == 0
    for label, key in frame._campo_a_clave.items():
        frame._campo_export.set(label)
        frame._actualizar_codigo()
        expected = frame._results[0].result[key]
        assert frame._resultado_preview.get('1.0', 'end-1c') == expected
        frame._copiar()
        assert frame.clipboard_get() == expected
    frame.destroy()


def test_abbreviated_code_still_copies_and_exports_full_text(ui_root, fixtures_dir, tmp_path, monkeypatch):
    frame = loaded_frame(ui_root, fixtures_dir)
    long_code = 'A' * 15_000
    result = dict(frame._results[0].result, base64=long_code)
    item = ItemResult(0, frame._imagenes[0], result=result)
    frame._results[0] = item
    frame._state.resultados = [result]
    frame._campo_export.set(t('lqip_field_base64'))
    frame._actualizar_codigo()
    assert len(frame._resultado_preview.get('1.0', 'end-1c')) == 12_000
    assert frame._lbl_abbreviated.winfo_manager() == 'grid'
    frame._copiar()
    assert frame.clipboard_get() == long_code
    output = tmp_path / 'full.txt'
    monkeypatch.setattr(frame_module.filedialog, 'asksaveasfilename', lambda **_: str(output))
    frame._guardar()
    assert long_code in output.read_text(encoding='utf-8')
    frame.destroy()


@pytest.mark.parametrize('width,blur', [('0', '2'), ('-1', '2'), ('2.5', '2'), ('20', '-2'), ('20', 'nan'), ('20', 'inf'), ('20', '')])
def test_invalid_parameters_block_generation(ui_root, width, blur):
    frame = LqipFrame(ui_root)
    frame._state.ancho_lqip.set(width)
    frame._state.blur.set(blur)
    assert frame._state.errores_validacion()
    assert frame._btn_procesar.cget('state') == 'disabled'
    frame._cambiar_modo(t('lqip_mode_b64'))
    assert not frame._state.errores_validacion()
    frame.destroy()


def test_modes_reuse_controls_and_preserve_parameters(ui_root):
    frame = LqipFrame(ui_root)
    frame._state.ancho_lqip.set('32')
    for _ in range(5):
        frame._cambiar_modo(t('lqip_mode_b64'))
        frame._cambiar_modo(t('lqip_mode_lqip'))
    assert frame._state.ancho_lqip.get() == '32'
    assert len(frame._frame_opciones_modo.winfo_children()) == 2
    frame.destroy()


@pytest.mark.parametrize('change', ['clear', 'reload', 'options'])
def test_generation_uses_snapshot_and_discards_stale_results(ui_root, fixtures_dir, monkeypatch, change):
    submitted = []
    class CapturedCoordinator:
        def submit(self, owner, label, work, success, failure):
            submitted.append((work, success))
            return True
    monkeypatch.setattr(LqipFrame, '_submit_job', lambda self, work, **options: CapturedCoordinator().submit(self, 'lqip', work, options['on_success'], options['on_error']))
    frame = LqipFrame(ui_root)
    path = str(fixtures_dir / 'sample.png')
    frame._cargar_imagenes([path])
    frame._procesar()
    frame._procesar()
    assert len(submitted) == 1
    work, callback = submitted[0]
    if change == 'clear':
        frame._limpiar()
    elif change == 'reload':
        frame._cargar_imagenes([str(fixtures_dir / 'sample.jpg')])
    else:
        frame._state.ancho_lqip.set('32')
    items = work()
    assert items[0].path == path
    assert items[0].dimensions[0] == 20
    callback(items)
    assert not frame._results
    assert not frame._state.resultados
    assert not frame._busy
    frame.destroy()


def test_failed_image_cannot_copy_or_export_and_can_be_replaced(ui_root, fixtures_dir):
    frame = LqipFrame(ui_root)
    paths = [str(fixtures_dir / 'missing.png')]
    frame._cargar_imagenes(paths)
    frame._finalizar(frame._revision, procesar_archivos(tuple(paths), frame._state.obtener_opciones()))
    frame._sources[0] = cargar_original(0, paths[0])
    frame._render_selected()
    assert frame._original_label.cget('text') == t('lqip_item_error')
    assert frame._btn_copiar.cget('state') == 'disabled'
    assert frame._btn_guardar.cget('state') == 'disabled'
    assert not frame._state.resultados
    paths = [str(fixtures_dir / 'sample.png')]
    frame._cargar_imagenes(paths)
    frame._finalizar(frame._revision, procesar_archivos(tuple(paths), frame._state.obtener_opciones()))
    assert frame._btn_copiar.cget('state') == 'normal'
    frame._limpiar()
    assert frame._selected_index is None
    assert frame._btn_guardar.cget('state') == 'disabled'
    frame.destroy()


@pytest.mark.parametrize('replacement', ['sample.jpg', 'sample.png'])
def test_loading_image_resets_all_settings_and_discards_result(ui_root, fixtures_dir, replacement):
    frame = loaded_frame(ui_root, fixtures_dir)
    frame._state.ancho_lqip.set('5000')
    frame._state.blur.set('25')
    frame._state.calidad_lqip.set(61)
    frame._state.calidad_b64.set(91)
    frame._cambiar_modo(t('lqip_mode_b64'))
    frame._campo_export.set(t('lqip_field_css_bg'))
    frame._cargar_imagenes([str(fixtures_dir / replacement)])
    assert frame._state.obtener_opciones() == {
        'modo': 'lqip', 'ancho': 20, 'blur': 2., 'calidad_lqip': 40, 'calidad_b64': 85,
    }
    assert frame._modo_visible.get() == t('lqip_mode_lqip')
    assert frame._obtener_clave_campo() == 'data_uri'
    assert not frame._results
    assert not frame._sources
    assert frame._btn_copiar.cget('state') == 'disabled'
    assert frame._btn_guardar.cget('state') == 'disabled'
    assert frame._lbl_input_name.cget('text') == replacement
    assert not frame._b64_options.winfo_manager()
    frame.destroy()


def test_selector_loads_only_one_image_and_cancel_preserves_current(ui_root, fixtures_dir, monkeypatch):
    frame = loaded_frame(ui_root, fixtures_dir)
    frame._state.ancho_lqip.set('32')
    before = frame._revision
    monkeypatch.setattr(frame_module.filedialog, 'askopenfilename', lambda **_: '')
    monkeypatch.setattr(frame_module.filedialog, 'askopenfilenames', lambda **_: pytest.fail('Multiple selection is forbidden'))
    frame._btn_seleccionar.invoke()
    assert frame._revision == before
    assert frame._state.ancho_lqip.get() == '32'
    path = str(fixtures_dir / 'sample.jpg')
    monkeypatch.setattr(frame_module.filedialog, 'askopenfilename', lambda **_: path)
    frame._btn_seleccionar.invoke()
    assert frame._imagenes == [path]
    assert frame._state.ancho_lqip.get() == '20'
    with pytest.raises(ValueError):
        frame._cargar_imagenes([path, path])
    assert frame._imagenes == [path]
    frame.destroy()


@pytest.mark.parametrize('mode', ['lqip_mode_lqip', 'lqip_mode_b64'])
def test_single_image_generation_and_exports(ui_root, fixtures_dir, tmp_path, monkeypatch, mode):
    import json

    frame = LqipFrame(ui_root)
    path = str(fixtures_dir / 'sample.png')
    frame._cargar_imagenes([path])
    frame._cambiar_modo(t(mode))
    items = procesar_archivos(tuple(frame._imagenes), frame._state.obtener_opciones())
    frame._finalizar(frame._revision, items)
    assert len(frame._state.resultados) == 1
    assert frame._btn_guardar.cget('state') == 'normal'
    expected_width = 20 if mode == 'lqip_mode_lqip' else cargar_original(0, path).dimensions[0]
    assert items[0].dimensions[0] == expected_width
    for suffix in ('txt', 'json'):
        output = tmp_path / ('result.' + suffix)
        monkeypatch.setattr(frame_module.filedialog, 'asksaveasfilename', lambda **_: str(output))
        frame._guardar()
        if suffix == 'json':
            assert json.loads(output.read_text(encoding='utf-8'))[0]['base64'] == items[0].result['base64']
        else:
            assert items[0].result['data_uri'] in output.read_text(encoding='utf-8')
    frame.destroy()


def test_reloading_rejects_old_original_preview(ui_root, fixtures_dir):
    frame = LqipFrame(ui_root)
    old_path = str(fixtures_dir / 'sample.png')
    frame._cargar_imagenes([old_path])
    revision = frame._source_revision
    old = cargar_original(0, old_path)
    new_path = str(fixtures_dir / 'sample.jpg')
    frame._cargar_imagenes([new_path])
    frame._source_queue.put((revision, old))
    frame.after_cancel(frame._source_job)
    frame._recibir_originales()
    assert all(source.path == new_path for source in frame._sources.values())
    frame.destroy()


def test_mapped_layout_and_hidden_controls_survive_scaling(ui_root, fixtures_dir):
    errors = []
    ui_root.report_callback_exception = lambda *args: errors.append(args)
    ui_root.geometry('1150x720')
    ui_root.deiconify()
    frame = loaded_frame(ui_root, fixtures_dir)
    frame.pack(fill='both', expand=True)
    try:
        for scale in (1, .75, .5, 1):
            ctk.set_widget_scaling(scale)
            ui_root.update()
            assert not frame._error_width.winfo_manager()
            assert not frame._error_blur.winfo_manager()
            assert not frame._b64_options.winfo_manager()
        assert frame._btn_guardar.winfo_rooty() + frame._btn_guardar.winfo_height() <= ui_root.winfo_rooty() + ui_root.winfo_height()
        frame._limpiar()
        ui_root.update()
        assert not errors
    finally:
        frame.destroy()
        ctk.set_widget_scaling(1)


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_translated_modes_and_formats_keep_internal_keys(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
    frame = LqipFrame(ui_root)
    assert frame._modo_visible.get() == t('lqip_mode_lqip')
    assert frame._state.modo.get() == 'lqip'
    frame._cambiar_modo(t('lqip_mode_b64'))
    assert frame._state.modo.get() == 'base64'
    frame._campo_export.set(t('lqip_field_base64'))
    assert frame._obtener_clave_campo() == 'base64'
    assert not frame._lbl_descripcion.cget('text').startswith('lqip_')
    frame.destroy()


@pytest.mark.parametrize('source_delivery', ['before_result', 'after_result'])
def test_long_code_button_and_select_all_copy_all_four_formats(
        ui_root, fixtures_dir, monkeypatch, source_delivery):
    # Controla cuándo llega el resultado; no dependas del tiempo del worker.
    source_loads = []
    monkeypatch.setattr(frame_module, 'Thread', lambda *, target, **_: SimpleNamespace(
        start=lambda: source_loads.append(target)))
    ui_root.deiconify()
    frame = loaded_frame(ui_root, fixtures_dir)
    frame.pack(fill='both', expand=True)

    def deliver_source():
        source_loads.pop()()
        frame.after_cancel(frame._source_job)
        frame._recibir_originales()

    if source_delivery == 'before_result':
        deliver_source()
    result = _construir_resultado('A' * 16000, 'photo.jpg')
    frame._finalizar(frame._revision, [ItemResult(0, frame._imagenes[0], result=result)])
    clipboard = {'text': ''}
    monkeypatch.setattr(frame, 'clipboard_clear', lambda: clipboard.update(text=''))
    monkeypatch.setattr(frame, 'clipboard_append', lambda text: clipboard.update(text=text))
    monkeypatch.setattr(frame, 'clipboard_get', lambda: clipboard['text'])
    # El formato inicial ya está seleccionado: pulsarlo no genera un evento de cambio.
    try:
        assert frame._campo_export.get() == t('lqip_field_data_uri')
        assert len(frame._resultado_preview.get('1.0', 'end-1c')) == 12000
        if source_delivery == 'after_result':
            deliver_source()
        for label, key in frame._campo_a_clave.items():
            frame._seg_formato._buttons_dict[label]._clicked()
            ui_root.update()
            expected = result[key]
            assert len(frame._resultado_preview.get('1.0', 'end-1c')) == 12000
            frame._btn_copiar._clicked()
            ui_root.update()
            assert frame.clipboard_get().replace('\r\n', '\n') == expected
            assert str(len(expected)) in frame._lbl_info.cget('text')
            textbox = frame._resultado_preview._textbox
            textbox.tag_add('sel', '1.0', 'end-1c')
            assert frame._copiar_desde_preview() == 'break'
            assert frame.clipboard_get().replace('\r\n', '\n') == expected
            textbox.tag_remove('sel', '1.0', 'end')
        # Seleccionar solo un fragmento conserva el comportamiento normal de Tk.
        textbox.tag_add('sel', '1.0', '1.8')
        assert frame._copiar_desde_preview() is None
    finally:
        frame.destroy()


def test_copy_does_not_report_success_if_clipboard_is_truncated(ui_root, fixtures_dir, monkeypatch):
    frame = loaded_frame(ui_root, fixtures_dir)
    monkeypatch.setattr(frame, 'clipboard_get', lambda: 'truncated')
    frame._copiar()
    assert frame._lbl_info.cget('text') == t('lqip_copy_failed')
    frame.destroy()


def test_active_lqip_rejects_programmatic_selection_and_clear(ui_root, fixtures_dir):
    from app.ui.operations import operations
    frame = LqipFrame(ui_root)
    path = str(fixtures_dir / 'sample.png')
    frame._cargar_imagenes([path])
    try:
        operation = operations.begin(frame, 'test')
        assert operation is not None
        frame._cargar_imagenes([str(fixtures_dir / 'sample.jpg')])
        frame._limpiar()
        assert frame._imagenes == [path]
    finally:
        if operations.active is not None and operations.active.owner is frame:
            operations.finish(operations.active.id)
        frame.destroy()
