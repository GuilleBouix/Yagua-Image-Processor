"""Stable viewport geometry, lazy tab renders and source identity regressions."""
from pathlib import Path
from time import monotonic, sleep

import customtkinter as ctk
from PIL import Image
import pytest

from app.modules.metadata_batch import leer_archivo
from app.translations import t
from app.ui.frames.metadata.frame import MetadataFrame
from app.ui.frames.metadata.state import path_key
from app.ui.frames.metadata.widgets import MetadataPreview
from app.ui.frames.lqip.frame import LqipFrame
from app.ui.frames.lqip.services import SourcePreview, ItemResult
from app.ui.operations import operations
from app.ui.rendering import StableRender


def pump(root, seconds=.14):
    end = monotonic() + seconds
    while monotonic() < end:
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        root.update()
        sleep(.002)


def wait_for(root, condition):
    deadline = monotonic() + 3
    while not condition() and monotonic() < deadline:
        pump(root, .04)
    assert condition()


def prepare_window(root, geometry):
    root.geometry(geometry)
    root.deiconify()
    width, height = map(int, geometry.split('x'))
    # CTk locks the old top-level dimensions for 1000 ms after scaling.
    # Match the real app: resize the window before entering a module.
    wait_for(root, lambda: (
        root.winfo_width() == int(root._apply_window_scaling(width))
        and root.winfo_height() == int(root._apply_window_scaling(height))))
    pump(root, .04)


@pytest.fixture(autouse=True)
def isolate_scaling(ui_root):
    # CTk menus retain scaling callbacks after their owner is destroyed.
    # Like the UI matrix, isolate each independently constructed scale.
    tracker = ctk.ScalingTracker
    callbacks = {window: list(items) for window, items in tracker.window_widgets_dict.items()}
    previous = tracker.widget_scaling
    yield
    tracker.window_widgets_dict = callbacks
    ctk.set_widget_scaling(previous)


class ClockViewport:
    """Controllable Tk timer and viewport for exact 16 ms assertions."""
    def __init__(self):
        self.now = 0
        self.jobs = {}
        self.serial = 0
        self.width, self.height, self.scale = 400, 180, 1
        self.mapped = True

    def bind(self, *_args, **_kwargs):
        pass

    def after(self, delay, callback):
        self.serial += 1
        self.jobs[self.serial] = (self.now + delay, callback)
        return self.serial

    def after_cancel(self, job):
        self.jobs.pop(job, None)

    def after_idle(self, callback):
        return self.after(0, callback)

    def advance(self, ms):
        end = self.now + ms
        while self.jobs and min(time for time, _ in self.jobs.values()) <= end:
            job = min(self.jobs, key=lambda key: self.jobs[key][0])
            self.now, callback = self.jobs.pop(job)
            callback()
        self.now = end

    def winfo_ismapped(self):
        return self.mapped

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height

    def _get_widget_scaling(self):
        return self.scale


def test_two_equal_samples_coalesce_and_cancel():
    viewport = ClockViewport()
    draws = []
    renderer = StableRender(viewport, viewport, lambda size: draws.append((viewport.now, size)))
    for _ in range(100):
        renderer.request()
    assert len(viewport.jobs) == 1
    viewport.advance(16)
    assert not draws
    renderer.request()  # An unchanged Configure must not discard this sample.
    viewport.advance(16)
    assert draws == [(32, (400, 180, 1))]
    viewport.width = 500
    renderer.request()
    viewport.advance(31)
    assert len(draws) == 1
    viewport.advance(1)
    assert draws == [(32, (400, 180, 1)), (64, (500, 180, 1))]
    renderer.request()
    viewport.advance(16)
    renderer.set_visible(False)
    viewport.advance(100)
    assert len(draws) == 2 and not viewport.jobs
    viewport.width = 1
    renderer.set_visible(True)
    viewport.advance(100)
    assert len(draws) == 2 and viewport.jobs
    viewport.width, viewport.scale = 250, .5
    renderer.request()
    viewport.advance(44)
    assert draws[-1][1] == (250, 180, .5)
    viewport.mapped = False
    renderer.request()
    assert not viewport.jobs


@pytest.mark.parametrize('scale', [1, .75, .5])
@pytest.mark.parametrize('geometry', ['1360x720', '900x600'])
def test_metadata_first_tab_draws_never_resize_viewport(ui_root, monkeypatch, tmp_path, scale, geometry):
    ctk.set_widget_scaling(scale)
    prepare_window(ui_root, geometry)
    view = MetadataFrame(ui_root)
    view.pack(fill='both', expand=True)
    controller = view._collection
    queued = []
    monkeypatch.setattr(controller, 'enqueue', lambda kind, key: queued.append((kind, key)))
    path = tmp_path / 'photo.jpg'
    Image.new('RGB', (3200, 1800), 'teal').save(path)
    view._cargar_lote([str(path)])
    image = Image.new('RGB', (1024, 576), 'teal')
    controller.loaded(controller.epoch, controller.revision, path_key(path), (leer_archivo(str(path)), '', image, ''))
    draws = []
    for pane in view._previews:
        draw = pane.renderer.draw
        def trace(size, pane=pane, draw=draw):
            assert pane.winfo_ismapped() and pane.renderer.enabled
            before = (pane.viewport.winfo_width(), pane.viewport.winfo_height(),
                      pane.master.winfo_width(), pane.master.winfo_height())
            draw(size)
            ui_root.update_idletasks()
            assert before == (pane.viewport.winfo_width(), pane.viewport.winfo_height(),
                              pane.master.winfo_width(), pane.master.winfo_height())
            draws.append((pane, before))
        pane.renderer.draw = trace
    try:
        saved = {}
        for tab in (t('view'), t('edit'), t('clean_batch')):
            view._cambiar_tab(tab)
            active = next(p for p in view._previews if p.tab_frame is view._frames[tab])
            wait_for(ui_root, lambda: active.photo is not None and active.renderer.job is None)
            pump(ui_root)
            wait_for(ui_root, lambda: active.renderer.job is None)
            assert active.photo is not None
            assert active.source is image
            saved[tab] = (active.photo, active.signature)
            pane, before = draws[-1]
            assert pane is active
            assert before == (pane.viewport.winfo_width(), pane.viewport.winfo_height(),
                              pane.master.winfo_width(), pane.master.winfo_height())
            assert all(p.renderer.job is None for p in view._previews if p is not active)
        for tab in (t('view'), t('edit'), t('clean_batch')):
            view._cambiar_tab(tab)
            pump(ui_root)
            active = next(p for p in view._previews if p.tab_frame is view._frames[tab])
            photo, signature = saved[tab]
            if active.signature == signature:
                assert active.photo is photo
            # Re-selecting an already visible tab must always reuse its image.
            photo = active.photo
            view._cambiar_tab(tab)
            pump(ui_root)
            assert active.photo is photo
        # Coalescing can cancel redundant callbacks. Verify actual image reuse
        # and the one-timer invariant instead of a wall-clock callback count.
        assert all(p.renderer.job is None for p in view._previews)
        assert [kind for kind, _ in queued].count('active') == 1
        view.on_view_hidden()
        controller.render_previews()
        pump(ui_root)
        assert all(p.renderer.job is None for p in view._previews)
    finally:
        view.destroy()


@pytest.mark.parametrize('count', [1, 100])
def test_metadata_pending_identity_clear_and_tabs_do_not_reread_lot(ui_root, tmp_path, monkeypatch, count):
    view = MetadataFrame(ui_root)
    controller = view._collection
    queued = []
    monkeypatch.setattr(controller, 'enqueue', lambda kind, key: queued.append((kind, key)))
    paths = []
    for index in range(count):
        path = tmp_path / f'{index}.jpg'
        Image.new('RGB', (20, 40), 'red').save(path)
        paths.append(str(path))
    view._cargar_lote(paths)
    key = view._state.active
    old_revision = controller.revision
    source = Image.new('RGB', (20, 40), 'red')
    data = leer_archivo(paths[0])
    controller.loaded(controller.epoch, old_revision, key, (data, '', source, ''))
    assert view._preview_ver.source is source
    target = path_key(paths[-1])
    controller.activate(target, force=True)
    for tab in (t('edit'), t('clean_batch'), t('view')):
        view._cambiar_tab(tab)
        active = next(p for p in view._previews if p.tab_frame is view._frames[tab])
        assert active.source is None and active.photo is None
        assert active.name.cget('text') == Path(paths[-1]).name
        assert active.image.cget('text') == t('reading_metadata')
    controller.loaded(controller.epoch, old_revision, key, (data, '', source, ''))
    assert view._preview_ver.source is None
    controller.loaded(controller.epoch, controller.revision, target, (data, '', source, ''))
    assert view._preview_ver.source is source
    assert [kind for kind, _ in queued].count('active') == 2
    view._limpiar()
    controller.loaded(controller.epoch - 1, controller.revision - 1, target, (data, '', source, ''))
    assert all(p.source is None and p.renderer.job is None for p in view._previews)
    view.destroy()


def test_preview_pending_destroy_and_replacement(ui_root):
    prepare_window(ui_root, '800x600')
    preview = MetadataPreview(ui_root)
    preview.pack(fill='both', expand=True)
    preview.show('a.jpg', Image.new('RGB', (1000, 200)))
    wait_for(ui_root, lambda: preview.photo is not None)
    assert preview.photo is not None
    first = preview.photo
    preview.set_visible(False)
    preview.set_visible(True)
    pump(ui_root)
    assert preview.photo is first
    preview.show('b.jpg', Image.new('RGB', (200, 1000)))
    assert preview.photo is None
    preview.set_visible(False)
    pump(ui_root)
    assert preview.photo is None and preview.renderer.job is None
    preview.set_visible(True)
    ui_root.update_idletasks()
    assert preview.renderer.job is not None
    renderer = preview.renderer
    preview.destroy()
    pump(ui_root)
    assert renderer.closed and renderer.job is None


@pytest.mark.parametrize('scale', [1, .75, .5])
def test_lqip_mode_and_hidden_render_reuse(ui_root, scale):
    ctk.set_widget_scaling(scale)
    prepare_window(ui_root, '900x600')
    view = LqipFrame(ui_root)
    view.pack(fill='both', expand=True)
    view._imagenes = ['a.jpg']
    view._selected_index = 0
    image = Image.new('RGB', (420, 240), 'teal')
    view._sources[0] = SourcePreview(0, 'a.jpg', (420, 240), 100, 'JPEG', image)
    view._results[0] = ItemResult(0, 'a.jpg', dimensions=(20, 11), image=Image.new('RGB', (20, 11)))
    dimensions = []
    renderer = view._preview_renderers['original']
    draw = renderer.draw
    def trace(size):
        viewport = renderer.viewport
        before = (viewport.winfo_width(), viewport.winfo_height())
        draw(size)
        ui_root.update_idletasks()
        dimensions.append((before, (viewport.winfo_width(), viewport.winfo_height())))
    renderer.draw = trace
    try:
        view._render_selected()
        assert not view._display_images
        wait_for(ui_root, lambda: set(view._display_images) == {'input', 'original', 'output'})
        pump(ui_root)
        assert set(view._display_images) == {'input', 'original', 'output'}
        label = view._original_label
        view._cambiar_modo(t('lqip_mode_b64'))
        pump(ui_root)
        wait_for(ui_root, lambda: renderer.job is None)
        assert view._original_label is label
        viewport = renderer.viewport
        measurements = (viewport.winfo_width(), viewport.winfo_height(), view._get_widget_scaling())
        renderer.draw(measurements)
        original = view._display_images['original']
        renderer.draw(measurements)
        assert view._display_images['original'] is original
        assert dimensions and all(before == after for before, after in dimensions)
        view.on_view_hidden()
        previous_source = view._sources[0]
        view._sources[0] = SourcePreview(0, 'a.jpg', (240, 420), 100, 'JPEG', Image.new('RGB', (240, 420)))
        view._render_selected()
        pump(ui_root)
        assert 'original' not in view._display_images
        assert all(r.job is None for r in view._preview_renderers.values())
        # A -> B -> A while hidden must not reuse the signature of an evicted photo.
        view._sources[0] = previous_source
        view._render_selected()
        view.on_view_shown()
        wait_for(ui_root, lambda: 'original' in view._display_images)
        assert view._display_images['original'] is not original
        view._limpiar()
        pump(ui_root)
        assert not view._display_images
        assert all(before == after for before, after in dimensions)
    finally:
        view.destroy()
