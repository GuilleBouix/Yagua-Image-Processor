"""Pixel caching, incremental rendering and stale-delivery regressions."""
from time import monotonic, sleep
from threading import Event, get_ident

import customtkinter as ctk
from PIL import Image
import pytest

from app.ui.image_cache import ReducedImageCache, ImageRequests
from app.ui.rendering import VirtualRows, PooledRow, configure_changed
from app.ui.operations import operations


def pump(root, seconds=.15):
    deadline = monotonic() + seconds
    while monotonic() < deadline:
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        root.update()
        sleep(.002)


def test_cache_reuses_pixels_and_invalidates_modified_file(tmp_path):
    path = tmp_path / 'foto.png'
    Image.new('RGB', (100, 80), 'red').save(path)
    cache = ReducedImageCache()
    first = cache.load(path, (44, 44))
    assert cache.load(path, (44, 44)) is first
    Image.new('RGB', (102, 81), 'blue').save(path)
    second = cache.load(path, (44, 44))
    assert second is not first
    assert second.dimensions == (102, 81)
    assert second.image.getpixel((0, 0)) == (0, 0, 255)
    assert len(cache._entries) == 1
    cache.invalidate(path)
    assert cache.bytes == 0


def test_cache_is_lru_and_never_exceeds_pixel_budget(tmp_path):
    cache = ReducedImageCache(limit_bytes=800)
    paths = []
    for index in range(3):
        path = tmp_path / f'{index}.png'
        Image.new('RGB', (10, 10)).save(path)
        paths.append(path)
    first = cache.load(paths[0], (10, 10))
    cache.load(paths[1], (10, 10))
    assert cache.load(paths[0], (10, 10)) is first
    cache.load(paths[2], (10, 10))
    assert cache.bytes == 800
    assert all(key[0] != str(paths[1].resolve()) for key in cache._entries)
    oversized = cache.load(paths[0], (10, 10), mode='RGBA')
    assert oversized.image.mode == 'RGBA'
    assert cache.bytes <= cache.limit_bytes


def test_cache_preserves_orientation_and_uses_separate_bounds(tmp_path):
    path = tmp_path / 'vertical.jpg'
    exif = Image.Exif()
    exif[274] = 6
    Image.new('RGB', (80, 40)).save(path, exif=exif)
    cache = ReducedImageCache()
    first = cache.load(path, (40, 40))
    second = cache.load(path, (20, 20))
    assert first.image.size == (20, 40)
    assert second.image.size == (10, 20)
    assert first is not second


def test_cancelled_decoder_does_not_deliver_into_new_generation(ui_root, tmp_path, monkeypatch):
    import app.ui.image_cache as module
    path = tmp_path / 'cancel.png'
    Image.new('RGB', (80, 40)).save(path)
    entered, release = Event(), Event()
    original = module.image_cache.load
    def decode(path, bounds, **kwargs):
        entered.set()
        release.wait(3)
        return original(path, bounds, **kwargs)
    monkeypatch.setattr(module.image_cache, 'load', decode)
    requests = ImageRequests(ui_root)
    deliveries = []
    requests.request(path, (44, 44), lambda *args: deliveries.append(get_ident()))
    assert entered.wait(3)
    requests.cancel()
    release.set()
    pump(ui_root)
    assert deliveries == []
    requests.request(path, (44, 44), lambda *args: deliveries.append(get_ident()))
    pump(ui_root)
    assert deliveries == [get_ident()]


@pytest.mark.parametrize('scale', [1, .75, .5])
def test_virtual_rows_bounded_reused_and_scrolled(ui_root, scale):
    ui_root.geometry('900x600')
    ui_root.deiconify()
    ctk.set_widget_scaling(scale)
    try:
        container = ctk.CTkScrollableFrame(ui_root, height=220)
        container.pack(fill='both', expand=True)
        def factory(parent):
            row = PooledRow(parent)
            row.name_label = ctk.CTkLabel(row, text='')
            row.name_label.pack()
            return row
        def render(row, key):
            configure_changed(row.name_label, text=str(key))
        rows = VirtualRows(container, factory, render)
        rows.sync(range(500))
        pump(ui_root)
        assert 0 in rows.rows and len(rows.rows) < 35
        identities = {id(row) for row in rows.rows.values()}
        rows.sync(range(501))
        pump(ui_root)
        assert identities == {id(row) for row in rows.rows.values()}
        container._parent_canvas.yview_moveto(1)
        pump(ui_root)
        assert 500 in rows.rows
        assert len(rows.rows) + len(rows.pool) < 35
        assert identities & {id(row) for row in rows.rows.values()}
        rows.sync([])
        pump(ui_root)
        assert not rows.rows
        container.destroy()
    finally:
        ctk.set_widget_scaling(1)


def test_metadata_reuses_table_rows_and_inactive_tabs_stay_empty(ui_root):
    from app.ui.frames.metadata.frame import MetadataFrame
    from app.translations import t
    view = MetadataFrame(ui_root)
    view._renderizar_metadatos({'Autor': 'Uno'})
    label = view._metadata_rows[0][2]
    view._renderizar_metadatos({'Autor': 'Dos'})
    assert view._metadata_rows[0][2] is label
    assert label.cget('text') == 'Dos'
    view._renderizar_metadatos({})
    view._renderizar_metadatos({'Autor': 'Tres'})
    assert view._metadata_rows[0][2] is label
    assert view._collection.tab == t('view')
    assert all(not files.rows for files in view._file_views[1:])


def test_watermark_clean_preserves_module_and_controls(ui_root):
    from app.ui.frames.watermark.frame import WatermarkFrame
    view = WatermarkFrame(ui_root)
    button = view._btn_aplicar
    view._state.escala.set(70)
    view._limpiar()
    assert view.winfo_exists() and view._btn_aplicar is button
    assert view._state.escala.get() == 25
    assert not view._imagenes


def test_queue_delivery_yields_after_budget(monkeypatch):
    from app.ui.operations import OperationCoordinator
    import app.ui.operations as module
    coordinator = OperationCoordinator()
    clock = [0.]
    monkeypatch.setattr(module, 'perf_counter', lambda: clock[0])
    values = []
    def callback(index):
        values.append(index)
        clock[0] += .005
    for index in range(100):
        coordinator.post(object(), lambda index=index: callback(index))
    coordinator.drain()
    assert values == [0, 1]
    coordinator.drain()
    assert values == [0, 1, 2, 3]


def test_duplicate_thumbnail_requests_both_deliver_on_ui_thread(ui_root, tmp_path):
    path = tmp_path / 'duplicate.png'
    Image.new('RGB', (60, 30)).save(path)
    requests = ImageRequests(ui_root)
    delivered = []
    requests.request(path, (44, 44), lambda *_args: delivered.append(('first', get_ident())))
    requests.request(path, (44, 44), lambda *_args: delivered.append(('second', get_ident())))
    pump(ui_root, .3)
    assert delivered == [('first', get_ident()), ('second', get_ident())]


def test_resize_mode_reuses_entries_and_values(ui_root):
    from app.ui.frames.resize.frame import ResizeFrame
    from app.translations import t
    view = ResizeFrame(ui_root)
    view._actualizar_modo_resize(t('pixels'))
    entry = view._entry_ancho
    entry.insert(0, '1234')
    view._actualizar_modo_resize(t('percentage'))
    view._actualizar_modo_resize(t('pixels'))
    assert view._entry_ancho is entry and entry.get() == '1234'


def test_palette_reuses_swatches_when_colors_change_and_clear(ui_root):
    from app.ui.frames.palette.frame import PaletteFrame
    view = PaletteFrame(ui_root)
    view._renderizar_paleta([(255, 0, 0), (0, 255, 0)])
    first = view._swatch_pool[0]
    view._renderizar_paleta([(0, 0, 255)])
    assert view._swatch_pool[0] is first
    assert first[2].cget('text').upper() == '#0000FF'
    view._limpiar()
    view._renderizar_paleta([(255, 0, 0)])
    assert view._swatch_pool[0] is first


def test_palette_swatches_remain_equal_width(ui_root):
    from app.ui.frames.palette.frame import PaletteFrame
    ui_root.geometry('900x600')
    ui_root.deiconify()
    view = PaletteFrame(ui_root)
    view.pack(fill='both', expand=True)
    view._renderizar_paleta([(index * 30, 40, 80) for index in range(6)])
    pump(ui_root)
    widths = [col.winfo_width() for col, *_rest in view._swatch_pool]
    assert max(widths) - min(widths) <= 2, widths
