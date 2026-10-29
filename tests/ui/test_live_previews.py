"""Selection, asynchronous lifecycle and bounded layouts of module previews."""
from threading import Event
from pathlib import Path
from time import monotonic, sleep

import customtkinter as ctk
from PIL import Image
import pytest

from app.translations import t
from app.ui.frames.resize.frame import ResizeFrame
from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.operations import operations
from app.ui.preview import LivePreview


def pump(root, predicate, timeout=8):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        root.update()
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        if predicate():
            return
        sleep(.005)
    raise AssertionError('Preview did not reach the requested state')


def pump_stable_size(root, widget, timeout=8):
    """Wait for the geometry manager to report the same usable size twice."""
    previous = None
    unchanged_since = None

    def stable():
        nonlocal previous, unchanged_since
        size = widget.winfo_width(), widget.winfo_height()
        now = monotonic()
        if size[0] <= 1 or size[1] <= 1:
            previous = None
            unchanged_since = None
        elif size != previous:
            previous = size
            unchanged_since = now
        elif unchanged_since is not None and now - unchanged_since >= .016:
            return True
        return False

    pump(root, stable, timeout)


def pump_stable_geometry(root, *widgets, timeout=8):
    """Wait until the toplevel and its workspace children complete their layout."""
    previous = None
    unchanged_since = None

    def stable():
        nonlocal previous, unchanged_since
        if not root.winfo_ismapped():
            previous = None
            unchanged_since = None
            return False
        sizes = ((root.winfo_width(), root.winfo_height()),) + tuple(
            (widget.winfo_width(), widget.winfo_height()) for widget in widgets)
        now = monotonic()
        if any(width <= 1 or height <= 1 for width, height in sizes):
            previous = None
            unchanged_since = None
        elif sizes != previous:
            previous = sizes
            unchanged_since = now
        elif unchanged_since is not None and now - unchanged_since >= .016:
            return True
        return False

    pump(root, stable, timeout)


def pump_workspace_geometry(root, view, timeout=8):
    """Wait for the scrollable frame and both workspace columns to settle together."""
    widgets = [view, view._parent_canvas, view._workspace_host,
               view._workspace_left, view._workspace_right, view._preview,
               view._preview.viewport]
    pump_stable_geometry(root, *widgets, timeout=timeout)


def pictures(tmp_path, count=2):
    paths = []
    for i in range(count):
        path = tmp_path / f'imagen-{i}.png'
        Image.new('RGBA', (100 + i, 80), (200, 0, 0, 128)).save(path)
        paths.append(str(path))
    return paths


@pytest.mark.parametrize('geometry', ['1400x900', '900x600'])
@pytest.mark.parametrize('scale', [1, .75, .5])
def test_resize_tabs_selection_and_stable_viewport(ui_root, tmp_path, geometry, scale):
    ctk.set_widget_scaling(scale)
    try:
        ui_root.deiconify()
        ui_root.state('normal')
        ui_root.geometry(geometry)
        expected_width, expected_height = (int(value) for value in geometry.split('x'))
        pump(ui_root, lambda: (ui_root.winfo_width(), ui_root.winfo_height()) ==
             (expected_width, expected_height))
        view = ResizeFrame(ui_root)
        view.pack(fill='both', expand=True)
        pump_workspace_geometry(ui_root, view)
        paths = pictures(tmp_path, 100)
        view._cargar_imagenes(paths)
        pump(ui_root, lambda: view._preview.output_dimensions == (50, 40))
        pump_workspace_geometry(ui_root, view)
        pump(ui_root, lambda: view._viewport_height == max(
            view.winfo_reqheight(), view._parent_canvas.winfo_height()))
        assert view._viewport_height == max(view.winfo_reqheight(), view._parent_canvas.winfo_height())
        viewport = view._preview.viewport
        view._virtual_file_list.select((paths[1], 0))
        pump(ui_root, lambda: view._preview.applied_path == paths[1])
        pump_workspace_geometry(ui_root, view)
        size = viewport.winfo_width(), viewport.winfo_height()
        assert view._imagenes == paths
        view._tab.set(t('crop_tab'))
        view._cambiar_tab(t('crop_tab'))
        pump(ui_root, lambda: view._preview.output_dimensions == (80, 80))
        pump_workspace_geometry(ui_root, view)
        view._state.canvas_width_var.set('200')
        view._state.canvas_height_var.set('100')
        view._tab.set(t('canvas_tab'))
        view._cambiar_tab(t('canvas_tab'))
        pump(ui_root, lambda: view._preview.output_dimensions == (200, 100))
        pump_workspace_geometry(ui_root, view)
        assert (viewport.winfo_width(), viewport.winfo_height()) == size
        assert len(view._virtual_file_list.virtual.rows) < 35
        view._state.canvas_width_var.set('bad')
        assert view._preview.photo is None
        assert view._preview.image.cget('text') == t('invalid_dimensions')
        view._limpiar()
        assert view._preview.path == ''
        view._cargar_imagenes(paths[:1])
        view._tab.set(t('resize_tab'))
        view._cambiar_tab(t('resize_tab'))
        pump(ui_root, lambda: view._preview.photo is not None)
    finally:
        ctk.set_widget_scaling(1)


def test_stale_worker_hidden_view_and_clear(ui_root, tmp_path, monkeypatch):
    import app.ui.preview as preview_module
    ui_root.deiconify()
    panel = LivePreview(ui_root)
    panel.pack(fill='both', expand=True)
    paths = pictures(tmp_path)
    paths = [Path(path).as_posix() for path in paths]
    entered, release = Event(), Event()
    original_render = preview_module.render_pixels
    calls = []

    def blocked(source, *args):
        calls.append(source.signature[0])
        if len(calls) == 1:
            entered.set()
            assert release.wait(8)
        return original_render(source, *args)
    monkeypatch.setattr(preview_module, 'render_pixels', blocked)
    panel.show(paths[0])
    pump(ui_root, entered.is_set)
    panel.show(paths[1])
    panel.set_visible(False)
    release.set()
    pump(ui_root, lambda: not panel._working)
    assert panel.photo is None
    assert len(calls) == 1
    panel.set_visible(True)
    pump(ui_root, lambda: panel.applied_path == paths[1])
    assert len(calls) == 2
    panel.show()
    assert panel.photo is None
    assert panel.applied_path == ''


def test_remove_bg_reads_only_saved_results_and_keeps_failed_original(ui_root, tmp_path, monkeypatch):
    monkeypatch.setattr('app.ui.frames.remove_bg.frame.estado_rembg', lambda: (True, None))
    monkeypatch.setattr('app.ui.frames.remove_bg.frame.modelo_descargado', lambda: True)
    ui_root.deiconify()
    view = RemoveBgFrame(ui_root)
    view.pack(fill='both', expand=True)
    pump(ui_root, lambda: hasattr(view, '_preview'))
    paths = pictures(tmp_path)
    view._cargar_imagenes(paths)
    pump(ui_root, lambda: view._preview.applied_path == paths[0])
    output = tmp_path / 'guardada.png'
    Image.new('RGBA', (60, 40), (0, 0, 255, 0)).save(output)
    result = {'ok': 1, 'errores': 1, 'resultados': [
        dict(estado='saved', ruta_entrada=str(Path(paths[0])), ruta_salida=str(output), tam_original=100,
             tam_resultado=50, reemplazado=False),
        dict(estado='error', ruta_entrada=str(Path(paths[1])), error='invalid_dimensions')], 'fallos': []}
    view._finish_save(result)
    pump(ui_root, lambda: view._preview.applied_path == str(output))
    assert t('preview_result') in view._preview.name.cget('text')
    view._virtual_file_list.select((paths[1], 0))
    pump(ui_root, lambda: view._preview.applied_path == paths[1])
    assert t('invalid_dimensions') in view._preview.info.cget('text')
    # Overwriting refreshes the original thumbnail and uses the newly saved pixels.
    Image.new('RGBA', (30, 20), 'green').save(paths[0])
    result['errores'] = 0
    result['resultados'] = [dict(estado='saved', ruta_entrada=paths[0], ruta_salida=paths[0],
                                tam_original=100, tam_resultado=50, reemplazado=True)]
    view._finish_save(result)
    view._virtual_file_list.select((paths[0], 0))
    pump(ui_root, lambda: view._preview.applied_path == paths[0] and view._preview.output_dimensions == (30, 20))
    view._limpiar()
    assert not view._preview_outputs
    view._cargar_imagenes(paths[:1])
    pump(ui_root, lambda: view._preview.applied_path == paths[0])


def test_unreadable_preview_cannot_replace_next_file(ui_root, tmp_path):
    panel = LivePreview(ui_root)
    panel.pack(fill='both', expand=True)
    ui_root.deiconify()
    panel.show(str(tmp_path / 'missing.png'))
    pump(ui_root, lambda: panel.image.cget('text') == t('preview_error'))
    assert panel.photo is None
    path = pictures(tmp_path, 1)[0]
    panel.show(path)
    pump(ui_root, lambda: panel.applied_path == path)


def test_canvas_sliders_and_manual_dimensions_stay_in_sync(ui_root, tmp_path):
    ui_root.deiconify()
    view = ResizeFrame(ui_root)
    view.pack(fill='both', expand=True)
    view._cargar_imagenes(pictures(tmp_path, 1))
    view._tab.set(t('canvas_tab'))
    view._cambiar_tab(t('canvas_tab'))
    pump(ui_root, lambda: view._preview.output_dimensions == (1080, 1080))
    width = view._canvas_sliders['width']
    height = view._canvas_sliders['height']
    width.cget('command')(640)
    height.cget('command')(480)
    assert view._canvas_ancho.get() == '640'
    assert view._canvas_alto.get() == '480'
    pump(ui_root, lambda: view._preview.output_dimensions == (640, 480))
    view._state.canvas_width_var.set('20000')
    assert width.get() == 20000
    assert width.cget('to') == 20000
    pump(ui_root, lambda: view._preview.output_dimensions == (20000, 480))
    view._state.canvas_width_var.set('')
    assert view._preview.photo is None
    view._state.canvas_width_var.set('320')
    assert width.get() == 320
    pump(ui_root, lambda: view._preview.output_dimensions == (320, 480))


def test_remove_bg_real_save_flow_accepts_dialog_path_separators(ui_root, tmp_path, monkeypatch):
    from app.utils.saving import plan_outputs, run_plan
    monkeypatch.setattr('app.ui.frames.remove_bg.frame.estado_rembg', lambda: (True, None))
    monkeypatch.setattr('app.ui.frames.remove_bg.frame.modelo_descargado', lambda: True)
    ui_root.deiconify()
    view = RemoveBgFrame(ui_root)
    view.pack(fill='both', expand=True)
    pump(ui_root, lambda: hasattr(view, '_preview'))
    source = Path(pictures(tmp_path, 1)[0])
    view._cargar_imagenes([source.as_posix()])
    destination = tmp_path / 'output'
    destination.mkdir()
    def process(paths, folder, **kwargs):
        def save(source, target):
            Image.new('RGBA', (100, 80), (0, 255, 0, 0)).save(target, 'PNG')
        return run_plan(kwargs['output_policy'], save)
    monkeypatch.setattr('app.ui.frames.remove_bg.frame.batch_quitar_fondo', process)
    monkeypatch.setattr(view, '_prepare_save', lambda paths, fmt, proceed:
                        proceed(str(destination), plan_outputs(paths, destination, 'copies', fmt)))
    view._procesar()
    output = str(destination / source.name)
    pump(ui_root, lambda: view._preview.applied_path == output)
    assert t('preview_result') in view._preview.name.cget('text')
    assert Image.open(output).getchannel('A').getextrema() == (0, 0)
