"""Palette collection navigation, stale deliveries, exports and small windows."""

from threading import Event

import customtkinter as ctk
import pytest
from PIL import Image

from app.modules.palette_batch import path_key
from app.translations import t
from app.ui.frames.palette.frame import PaletteFrame
from app.ui.operations import operations
from tests.ui.test_live_previews import pump


def sources(tmp_path, count=2):
    paths = [tmp_path / f'image-{index}.png' for index in range(count)]
    for index, path in enumerate(paths):
        Image.new('RGB', (16, 12), 'blue' if index % 2 else 'red').save(path)
    return paths


def test_successive_loads_selection_color_count_and_clear(ui_root, tmp_path):
    view = PaletteFrame(ui_root)
    paths = sources(tmp_path)
    view._add_images(paths[:1])
    pump(ui_root, lambda: view._state.paleta == [(255, 0, 0)])
    first = view._swatch_pool[0]
    view._add_images(paths)
    assert len(view._state.paths) == 2
    assert view._state.ruta == path_key(paths[0])
    assert view._state.paleta == [(255, 0, 0)]
    view._files.select((path_key(paths[1]), 0))
    pump(ui_root, lambda: view._state.paleta == [(0, 0, 255)])
    view._seg_n.set('12')
    view._auto_extraer()
    pump(ui_root, lambda: view._state.paleta == [(0, 0, 255)])
    assert view._swatch_pool[0] is first
    view._limpiar()
    assert not view._state.paths and not view._state.paleta
    assert view._btn_guardar_todas.cget('state') == 'disabled'
    view._add_images(paths[:1])
    pump(ui_root, lambda: view._state.paleta == [(255, 0, 0)])
    assert view._swatch_pool[0] is first


def test_late_extraction_after_clear_and_reload_is_ignored(ui_root, tmp_path, monkeypatch):
    paths = sources(tmp_path)
    view = PaletteFrame(ui_root)
    started, release = Event(), Event()
    original = view._cache.extract
    def slow(path, count):
        started.set()
        assert release.wait(5)
        return original(path, count)
    monkeypatch.setattr(view._cache, 'extract', slow)
    try:
        view._add_images(paths[:1])
        pump(ui_root, started.is_set)
        view._files.sync([path_key(path) for path in paths])
        view._files.select((path_key(paths[1]), 0))
        view._limpiar()
        view._add_images(paths[1:])
        release.set()
        pump(ui_root, lambda: view._state.paleta == [(0, 0, 255)])
        assert view._state.ruta == path_key(paths[1])
        assert len(view._state.paths) == 1
    finally:
        release.set()


def test_save_all_reuses_inspected_palettes_and_cancel(ui_root, tmp_path, monkeypatch):
    view = PaletteFrame(ui_root)
    paths = sources(tmp_path)
    broken = tmp_path / 'broken.png'
    broken.write_bytes(b'bad')
    view._add_images(paths + [broken])
    pump(ui_root, lambda: bool(view._state.paleta))
    view._files.select((path_key(paths[1]), 0))
    pump(ui_root, lambda: view._state.paleta == [(0, 0, 255)])
    view._files.select((path_key(paths[0]), 0))
    pump(ui_root, lambda: view._state.paleta == [(255, 0, 0)])
    folder = tmp_path / 'exports'
    folder.mkdir()
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.askdirectory', lambda **kw: '')
    view._guardar_todas()
    assert not list(folder.iterdir())
    assert not operations.is_busy()
    from app.modules import palette_batch
    original = palette_batch.extraer_paleta
    calls = []
    def extract(path, count):
        calls.append(path)
        return original(path, count)
    monkeypatch.setattr(palette_batch, 'extraer_paleta', extract)
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.askdirectory', lambda **kw: str(folder))
    view._guardar_todas()
    pump(ui_root, lambda: len(list(folder.glob('*.png'))) == 2 and not operations.is_busy())
    assert calls == [path_key(broken)]
    assert len({row['output'] for row in view._results if row['output']}) == 2
    assert sum(bool(row['error']) for row in view._results) == 1
    assert t('status_errors').format(count=1) in view._lbl_info.cget('text')
    assert view._btn_guardar.cget('state') == 'normal'
    assert view._full_overlay_bar.cget('mode') == 'indeterminate'


def test_individual_save_protects_inputs_and_refreshes_changed_source(ui_root, tmp_path, monkeypatch):
    view = PaletteFrame(ui_root)
    path = sources(tmp_path, 1)[0]
    view._add_images([path])
    pump(ui_root, lambda: bool(view._state.paleta))
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.asksaveasfilename', lambda **kw: str(path))
    original = path.read_bytes()
    view._guardar_imagen()
    assert path.read_bytes() == original
    assert view._lbl_info.cget('text') == t('palette_source_protected')
    Image.new('RGB', (16, 12), 'blue').save(path)
    output = tmp_path / 'saved.png'
    monkeypatch.setattr('app.ui.frames.palette.frame.filedialog.asksaveasfilename', lambda **kw: str(output))
    view._guardar_imagen()
    pump(ui_root, lambda: output.exists() and not operations.is_busy())
    with Image.open(output) as exported:
        assert exported.getpixel((30, 30)) == (0, 0, 255)


@pytest.mark.parametrize('geometry', ['1400x900', '900x600'])
@pytest.mark.parametrize('scale', [1, .75, .5])
def test_batch_layout_keeps_swatches_and_list_bounded(ui_root, tmp_path, geometry, scale):
    ctk.set_widget_scaling(scale)
    view = None
    try:
        width, height = map(int, geometry.split('x'))
        ui_root.minsize(width, height)
        ui_root.maxsize(width, height)
        ui_root.geometry(geometry)
        ui_root.deiconify()
        view = PaletteFrame(ui_root)
        view.pack(fill='both', expand=True)
        view._add_images(sources(tmp_path, 100))
        pump(ui_root, lambda: bool(view._state.paleta))
        assert view._frame_preview.winfo_width() > 300, (ui_root.winfo_width(), view.winfo_width(), view._frame_preview.winfo_width())
        view._renderizar_paleta([(index * 20, 40, 80) for index in range(12)])
        ui_root.update_idletasks()
        assert len(view._files.virtual.rows) < 10
        assert view._swatch_host.winfo_width() < ui_root.winfo_width()
        assert view._btn_guardar_todas.winfo_rootx() + view._btn_guardar_todas.winfo_width() <= (
            ui_root.winfo_rootx() + ui_root.winfo_width())
        assert not hasattr(view, '_btn_extraer_todas')
        assert [widget.grid_info()['row'] for widget in (
            view._btn_seleccionar, view._panel_paleta, view._frame_preview, view._actions
        )] == [1, 2, 3, 4]
        # A short window keeps the one-column layout accessible by scrolling.
        view._parent_canvas.yview_moveto(1)
        ui_root.update_idletasks()
        assert view._btn_guardar_todas.winfo_rooty() + view._btn_guardar_todas.winfo_height() <= (
            ui_root.winfo_rooty() + ui_root.winfo_height())
        assert len(view._swatch_pool) == 12
        # All copy buttons must remain inside the reserved palette at every
        # scale, even when fewer colors reuse columns from a 12-color palette.
        for count in (12, 4, 6, 8, 10):
            view._renderizar_paleta([(index * 20, 40, 80) for index in range(count)])
            ui_root.update_idletasks()
            for _, _, _, buttons in view._swatch_pool[:count]:
                assert buttons[-1].winfo_rooty() + buttons[-1].winfo_height() <= (
                    view._swatch_host.winfo_rooty() + view._swatch_host.winfo_height())
    finally:
        if view is not None:
            view.destroy()
        ctk.set_widget_scaling(1)
