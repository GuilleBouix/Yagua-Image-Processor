"""Pruebas de interfaz para resize frame y sus estados principales."""

from app.ui.frames.resize.frame import ResizeFrame
from app import translations
import pytest


def test_resize_frame_build(ui_root):
    frame = ResizeFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_tab")
    assert hasattr(frame, "_frames")


def test_custom_crop_mode_validation_and_save(ui_root, monkeypatch):
    from app.translations import t
    frame = ResizeFrame(ui_root)
    frame._state.crop_mode.set(t('crop_mode_dimensions'))
    frame._state.crop_width_var.set('80')
    frame._state.crop_height_var.set('60')
    ui_root.update_idletasks()
    assert frame._crop_dimension_controls.winfo_manager() == 'grid'
    assert frame._crop_ratio_controls.winfo_manager() == 'grid'
    assert frame._crop_visible_mode is True
    captures = []
    monkeypatch.setattr(frame, '_save_resize', lambda processor, options, *args: captures.append(options))
    frame._ejecutar_crop()
    assert captures == [dict(ancho=80, alto=60)]
    frame._state.crop_width_var.set('')
    frame._ejecutar_crop()
    assert len(captures) == 1
    assert frame._lbl_info.cget('text') == t('invalid_dimensions')
    frame._state.crop_mode.set(t('crop_mode_ratio'))
    assert frame._crop_options() == dict(ratio='1:1')
    assert frame._crop_ratio_controls.winfo_manager() == 'grid'
    assert frame._crop_dimension_controls.winfo_manager() == 'grid'
    assert frame._crop_visible_mode is False
    assert frame._state.crop_height_var.get() == '60'


def test_small_crop_is_reported_as_omitted(ui_root, tmp_path):
    from PIL import Image
    from app.modules.resize import batch_recortar
    from app.translations import t
    path = tmp_path / 'small.png'
    Image.new('RGB', (10, 10), 'red').save(path)
    frame = ResizeFrame(ui_root)
    frame._cargar_imagenes([str(path)])
    result = batch_recortar([str(path)], None, ancho=80, alto=60, output_policy='overwrite')
    frame._finish_save(result)
    assert frame._virtual_file_list.statuses[str(path)] == t('save_omitted') + ': ' + t('crop_too_large')
    assert frame._lbl_info.cget('text') == t('status_omitted').format(count=1)


@pytest.mark.parametrize('geometry', ['1400x900', '900x600'])
@pytest.mark.parametrize('scale', [1, .75, .5])
def test_crop_mode_switch_keeps_panels_mounted_and_layout_stable(ui_root, geometry, scale):
    import customtkinter as ctk
    from app.translations import t
    from tests.ui.test_live_previews import pump_workspace_geometry
    ctk.set_widget_scaling(scale)
    try:
        ui_root.deiconify()
        ui_root.state('normal')
        ui_root.geometry(geometry)
        view = ResizeFrame(ui_root)
        view.pack(fill='both', expand=True)
        view._tab.set(t('crop_tab'))
        view._cambiar_tab(t('crop_tab'))
        pump_workspace_geometry(ui_root, view)
        panels = (view._crop_ratio_controls, view._crop_dimension_controls)
        identities = tuple(tuple(panel.winfo_children()) for panel in panels)
        transitions = []
        for panel in panels:
            panel.bind('<Map>', lambda event: transitions.append('map'), add=True)
            panel.bind('<Unmap>', lambda event: transitions.append('unmap'), add=True)
        button_y = view._btn_crop.winfo_rooty()
        viewport_size = view._preview.viewport.winfo_width(), view._preview.viewport.winfo_height()
        for mode in ('crop_mode_dimensions', 'crop_mode_ratio') * 3:
            view._state.crop_mode.set(t(mode))
            pump_workspace_geometry(ui_root, view)
            assert view._btn_crop.winfo_rooty() == button_y
            assert (view._preview.viewport.winfo_width(), view._preview.viewport.winfo_height()) == viewport_size
            assert tuple(tuple(panel.winfo_children()) for panel in panels) == identities
            exact = mode == 'crop_mode_dimensions'
            assert all(int(entry._entry.cget('takefocus')) == int(exact) for entry in view._crop_entries)
        assert transitions == []
    finally:
        ctk.set_widget_scaling(1)


def test_crop_sliders_and_inputs_stay_synchronized(ui_root, tmp_path):
    from PIL import Image
    from tests.ui.test_live_previews import pump
    path = tmp_path / 'source.png'
    Image.new('RGB', (640, 480), 'red').save(path)
    frame = ResizeFrame(ui_root)
    frame._cargar_imagenes([str(path)])
    pump(ui_root, lambda: frame._crop_source_dimensions is not None)
    assert frame._state.crop_width_var.get() == '640'
    assert frame._state.crop_height_var.get() == '480'
    for key, variable in (('width', frame._state.crop_width_var),
                          ('height', frame._state.crop_height_var)):
        slider = frame._crop_sliders[key]
        slider.cget('command')(345.7)
        assert variable.get() == '346'
        assert slider.get() == 346
        variable.set('9000')
        assert slider.cget('to') == frame._crop_source_dimensions[key]
        assert slider.get() == frame._crop_source_dimensions[key]
        variable.set('')
        assert variable.get() == ''


@pytest.mark.parametrize('size,orientation,expected', [((300, 200), 1, (300, 200)),
    ((300, 200), 6, (200, 300)), ((1, 1), 1, (1, 1))])
def test_crop_selection_resets_limits_and_values(ui_root, tmp_path, size, orientation, expected):
    from PIL import Image
    from app.translations import t
    from tests.ui.test_live_previews import pump
    first, second = tmp_path / 'first.png', tmp_path / 'second.png'
    Image.new('RGB', (640, 480), 'red').save(first)
    exif = Image.Exif()
    exif[274] = orientation
    Image.new('RGB', size, 'blue').save(second, exif=exif)
    ui_root.deiconify()
    ui_root.state('normal')
    ui_root.geometry('900x600')
    view = ResizeFrame(ui_root)
    view.pack(fill='both', expand=True)
    view._cargar_imagenes([str(first), str(second)])
    view._tab.set(t('crop_tab'))
    view._cambiar_tab(t('crop_tab'))
    view._state.crop_mode.set(t('crop_mode_dimensions'))
    pump(ui_root, lambda: view._preview.output_dimensions == (640, 480))
    view._state.crop_width_var.set('80')
    view._virtual_file_list.select((str(second), 0))
    pump(ui_root, lambda: view._preview.output_dimensions == expected
         and view._preview.applied_path == str(second))
    assert (view._state.crop_width_var.get(), view._state.crop_height_var.get()) == tuple(map(str, expected))
    assert (view._crop_sliders['width'].cget('to'), view._crop_sliders['height'].cget('to')) == expected
    # Una respuesta de la selección anterior no cambia los límites vigentes.
    view._crop_source_loaded(str(first), None, OSError('late'))
    assert view._state.crop_width_var.get() == str(expected[0])
    view._limpiar()
    view._crop_source_loaded(str(second), None, OSError('late'))
    assert view._state.crop_width_var.get() == ''
    assert view._crop_source_dimensions is None


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_result_uses_current_language(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
    frame = ResizeFrame(ui_root)
    for count in (0, 1, 2):
        frame._finalizar(frame._btn_canvas, 'Canvas', count, 0)
        expected = translations.t('status_processed').format(count=count) if count else translations.t('status_empty')
        assert frame._lbl_info.cget('text') == expected
