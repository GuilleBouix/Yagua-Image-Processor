"""Arranque sin red, construcción progresiva y navegación reanudable."""
from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys
import textwrap
from threading import get_ident
from time import monotonic, sleep
from types import SimpleNamespace

import customtkinter as ctk
import pytest

from app.translations import AVAILABLE_LANGUAGES, t
from app.ui.building import BuildTask, finish, stepwise, steps_for
from app.ui import module_registry, startup
from app.ui.lifetime import UiLifetime


def wait(root, condition, timeout=20):
    deadline = monotonic() + timeout
    while not condition() and monotonic() < deadline:
        root.update()
        sleep(.002)
    assert condition()


class PendingImports:
    def __init__(self):
        self.pending = {}

    def request(self, key, path, callback):
        self.pending[key] = callback

    def deliver(self, key, cls=None, error=None):
        self.pending.pop(key)(cls, error)


class TinyFrame(UiLifetime, ctk.CTkFrame):
    def __init__(self, parent, *, defer_build=False):
        super().__init__(parent)
        self.build_ready = False
        self.built = []
        self._build_iterator = self.build()
        if not defer_build:
            finish(self._build_iterator)

    def build(self):
        for number in range(15):
            self.built.append(number)
            yield
        self.build_ready = True


def preloader(root, monkeypatch, keys=('convert', 'compress')):
    specs = [module_registry.get_module_spec(key) for key in keys]
    monkeypatch.setattr(startup, 'iter_enabled_modules', lambda: iter(specs))
    content = ctk.CTkFrame(root)
    content.pack(fill='both', expand=True)
    window = SimpleNamespace(content=content, frames=dict.fromkeys(keys),
        winfo_toplevel=lambda: root, _get_view_host=lambda frame: frame,
        _notify_view_hidden=lambda frame: None)
    imports = PendingImports()
    events = []
    loader = startup.ModulePreloader(window, imports,
        lambda *args: events.append(args), lambda: events.append('done'))
    return loader, imports, window, events


def test_stepwise_preserves_return_values_and_synchronous_api():
    class Builder:
        @stepwise
        def build(self, value):
            yield
            return value
    builder = Builder()
    assert builder.build(42) == 42
    assert finish(steps_for(builder.build, 23)) == 23


def test_builder_pause_resume_cancel_and_failure(ui_root):
    events = []
    def steps():
        events.append('first')
        task.pause()
        yield
        events.append('second')
        yield
    task = BuildTask(ui_root, steps(), lambda: events.append('done'), pytest.fail)
    task.resume()
    wait(ui_root, lambda: task.paused)
    assert events == ['first'] and task.job is None
    task.resume()
    wait(ui_root, lambda: task.finished)
    assert events == ['first', 'second', 'done']
    cancelled = BuildTask(ui_root, (item for item in ()), lambda: pytest.fail('cancelled task ran'), pytest.fail)
    cancelled.cancel()
    cancelled.resume()
    assert cancelled.job is None
    def broken():
        yield
        raise ValueError('broken')
    failures = []
    failed = BuildTask(ui_root, broken(), lambda: pytest.fail('unexpected completion'), failures.append)
    failed.resume()
    wait(ui_root, lambda: failed.finished)
    assert isinstance(failures[0], ValueError)


def test_cooperative_batches_yield_at_eight_ms(monkeypatch):
    now, jobs, sizes, built = [0.0], [], [], []
    monkeypatch.setattr('app.ui.building.perf_counter', lambda: now[0])
    def schedule(_delay, callback):
        jobs.append(callback)
        return len(jobs)
    owner = SimpleNamespace(after=schedule, after_idle=lambda callback: schedule(0, callback))
    def steps():
        for number in range(10):
            built.append(number)
            now[0] += .003
            yield
    task = BuildTask(owner, steps(), lambda: None, pytest.fail)
    task.resume()
    while jobs:
        before = len(built)
        jobs.pop(0)()
        if len(built) != before:
            sizes.append(len(built) - before)
    assert sizes == [3, 3, 3, 1] and task.finished


def test_preload_policy_is_opt_in_and_excludes_ai():
    specs = module_registry.iter_all_modules()
    assert len([spec for spec in specs if spec.preload_ui]) == 9
    assert not module_registry.ModuleSpec('future', 'future', '', '').preload_ui
    assert not any(spec.preload_ui for spec in specs if spec.key in ('ocr', 'remove_bg'))


def test_sidebar_changes_only_the_previous_and_new_selection(monkeypatch):
    from app.ui import sidebar
    painted = []
    monkeypatch.setattr(sidebar, 'tintar_icono', lambda *args: args)
    buttons = {key: {'btn': SimpleNamespace(set_selected=lambda _selected, _image, key=key: painted.append(key)),
                     'icon_path': key} for key in ('convert', 'compress', 'metadata')}
    view = SimpleNamespace(buttons=buttons, _active_key=None)
    sidebar.Sidebar.set_active(view, None)
    assert not painted
    sidebar.Sidebar.set_active(view, 'convert')
    assert painted == ['convert']
    sidebar.Sidebar.set_active(view, 'compress')
    assert painted == ['convert', 'convert', 'compress']
    sidebar.Sidebar.set_active(view, 'compress')
    assert painted == ['convert', 'convert', 'compress']


def test_lazy_exports_do_not_import_frames_or_ai_in_fresh_process():
    code = """
import sys
import app.ui.frames as frames
assert not any(name.startswith('app.ui.frames.') for name in sys.modules)
assert frames.ConvertFrame.__name__ == 'ConvertFrame'
assert not any(name in sys.modules for name in (
    'app.ui.frames.ocr.frame', 'app.ui.frames.remove_bg.frame',
    'easyocr', 'rembg', 'torch', 'onnxruntime'))
"""
    subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[2], check=True)


@pytest.mark.parametrize('scale', [1, .75, .5])
@pytest.mark.parametrize('early', [False, True])
def test_real_entrypoint_mainloop_displays_splash_and_home(tk_session, scale, early):
    # Llamar update() antes del mainloop ocultaba la inicialización de la barra
    # de título y withdraw de CTk en Windows. Prueba directamente app.main.main.
    code = f'scale = {scale!r}\nearly = {early!r}\n' + textwrap.dedent('''
        import ctypes
        import json
        import logging
        from pathlib import Path
        import sys
        from tempfile import TemporaryDirectory
        from time import monotonic
        import customtkinter as ctk
        import requests
        import app.utils.settings as settings
        with TemporaryDirectory(prefix='yagua-mainloop-') as directory:
            settings.settings_path = lambda: Path(directory) / 'settings.json'
            settings.settings_path().write_text(json.dumps({'ui_scale': round(scale * 100)}))
            def offline(*args, **kwargs):
                raise requests.ConnectionError('offline startup regression')
            requests.sessions.Session.request = offline
            from app import main as entrypoint
            OriginalApp = entrypoint.YaguaApp
            states, errors, summary = [], [], {}
            class ObservedApp(OriginalApp):
                def __init__(self):
                    super().__init__()
                    self.report_callback_exception = lambda *details: errors.append(str(details))
                    self.deadline = monotonic() + 25
                    self.pressed = False
                    self.after(30, self.observe)
                def observe(self):
                    mapped = bool(self.winfo_ismapped())
                    if sys.platform == 'win32':
                        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                        mapped = mapped and bool(ctypes.windll.user32.IsWindowVisible(hwnd))
                    splash = bool(self._startup.screen.winfo_ismapped())
                    states.append((mapped, splash, self.state()))
                    if early and splash and not self.pressed:
                        self._startup.screen.button.invoke()
                        self.pressed = True
                    if self.ready or monotonic() > self.deadline:
                        summary.update(ready=self.ready, mapped=mapped, pressed=self.pressed,
                                       entered_early=self._startup.entered_early)
                        if self.ready:
                            summary['frames'] = [key for key, value in self.main_window.frames.items() if value is not None]
                            summary['home'] = self.main_window._active_view is self.main_window._home
                            summary['errors'] = self._startup.preloader.errors
                        self.destroy()
                    else:
                        self.after(30, self.observe)
            entrypoint.YaguaApp = ObservedApp
            try:
                entrypoint.main()
            finally:
                logging.shutdown()
            assert any(mapped and splash for mapped, splash, state in states), states
            assert summary['ready'] and summary['mapped'] and summary['home'], summary
            assert not summary['errors'] and not errors, (summary, errors)
            assert summary['pressed'] == early
            if not early:
                assert len(summary['frames']) == 9, summary
            if sys.platform == 'win32':
                assert states[-1][2] == 'zoomed', states
            assert not any(name in sys.modules for name in (
                'app.modules.ocr', 'app.modules.remove_bg', 'easyocr', 'rembg', 'torch', 'onnxruntime'))
            print('MAINLOOP_OK')
    ''')
    result = subprocess.run([sys.executable, '-c', code],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'MAINLOOP_OK' in result.stdout


def test_imports_run_off_tk_and_delivery_runs_on_ui(ui_root, monkeypatch):
    main_thread = get_ident()
    worker_threads, delivered = [], []
    monkeypatch.setattr(startup, 'import_module',
        lambda path: (worker_threads.append(get_ident()) or SimpleNamespace(Frame=TinyFrame)))
    imports = startup.Imports(ui_root)
    try:
        imports.request('convert', 'fake:Frame', lambda *result: delivered.append((get_ident(), result)))
        wait(ui_root, lambda: bool(delivered))
        assert worker_threads[0] != main_thread
        assert delivered == [(main_thread, (TinyFrame, None))]
        imports.request('compress', 'fake:Frame', lambda *_: pytest.fail('late result delivered'))
        imports.close()
        ui_root.update()
        assert not imports.pending and imports.job is None
    finally:
        imports.close()


def test_partial_construction_pauses_resumes_and_reuses_instance(ui_root, monkeypatch):
    ui_root.deiconify()
    loader, imports, window, _ = preloader(ui_root, monkeypatch)
    loader.ensure('convert')
    imports.deliver('convert', TinyFrame)
    frame = loader.partials['convert']
    next(frame._build_iterator)
    loader.pause()
    ui_root.update()
    assert frame.built == [0] and not frame.winfo_manager()
    ready = []
    loader.ensure('convert', ready.append)
    wait(ui_root, lambda: bool(ready))
    assert ready == [frame] and window.frames['convert'] is frame
    loader.ensure('convert', ready.append)
    assert ready == [frame, frame] and len(frame.built) == 15
    loader.close()


@pytest.mark.parametrize('constructor_failure', [False, True])
def test_failure_continues_cleans_partial_and_can_retry(ui_root, monkeypatch, constructor_failure):
    ui_root.deiconify()
    loader, imports, window, events = preloader(ui_root, monkeypatch)
    class Broken(TinyFrame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if constructor_failure:
                raise ValueError('constructor failed')

        def build(self):
            yield
            raise ValueError('control failed')
    loader.start()
    imports.deliver('convert', Broken)
    wait(ui_root, lambda: 'compress' in imports.pending)
    assert 'convert' in loader.errors and 'convert' not in loader.partials
    assert not window.content.winfo_children()
    imports.deliver('compress', TinyFrame)
    wait(ui_root, lambda: 'done' in events)
    assert window.frames['compress'].build_ready
    loader.classes['convert'] = TinyFrame
    ready = []
    loader.ensure('convert', ready.append)
    wait(ui_root, lambda: bool(ready))
    assert not loader.errors
    loader.close()


def test_late_import_is_cached_without_constructing_wrong_view(ui_root, monkeypatch):
    loader, imports, window, _ = preloader(ui_root, monkeypatch)
    loader.ensure('convert')
    loader.ensure('compress')
    imports.deliver('convert', TinyFrame)
    assert not loader.partials and window.frames['convert'] is None
    loader.close()
    imports.deliver('compress', TinyFrame)
    assert not loader.partials


@pytest.mark.parametrize('phase', ['imports', 'shell', 'module'])
def test_closing_during_startup_cancels_jobs(ui_root, monkeypatch, phase):
    imports = PendingImports()
    imports.close = lambda: imports.pending.clear()
    monkeypatch.setattr(startup, 'Imports', lambda owner: imports)
    ui_root.ready = False
    ui_root.main_window = None
    coordinator = startup.ApplicationStartup(ui_root)
    coordinator.start()
    if phase != 'imports':
        from app.ui.main_window import MainWindow
        imports.deliver('__shell__', MainWindow)
        if phase == 'module':
            ui_root.deiconify()
            wait(ui_root, lambda: coordinator.preloader is not None)
            key = coordinator.preloader.current
            imports.deliver(key, TinyFrame)
    coordinator.close()
    assert not imports.pending
    if coordinator.shell_task:
        assert coordinator.shell_task.job is None
    if coordinator.preloader:
        assert all(task.job is None for task in coordinator.preloader.tasks.values())
    if ui_root.main_window:
        ui_root.main_window.destroy()
    ui_root.update()
    assert not ui_root.ready
    coordinator.screen.destroy()


def test_shell_failure_is_visible_and_closes_cleanly(ui_root, monkeypatch):
    shown, closed = [], []
    ui_root.ready = False
    coordinator = startup.ApplicationStartup(ui_root)
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *args, **kwargs: shown.append(args))
    monkeypatch.setattr(ui_root, 'destroy', lambda: closed.append(True))
    coordinator._shell_imported(None, RuntimeError('shell failed'))
    assert shown and closed == [True] and not ui_root.ready
    coordinator.close()
    coordinator.screen.destroy()


@pytest.mark.parametrize('early_stage', ['imports', 'shell', 'module', 'complete'])
def test_real_startup_early_entry_navigation_and_close(ui_root, monkeypatch, tmp_path, early_stage):
    from app.ui.main_window import MainWindow
    from app.utils import settings
    monkeypatch.setattr(settings, 'settings_path', lambda: tmp_path / 'settings.json')
    monkeypatch.setattr(module_registry, 'settings_path', settings.settings_path)
    monkeypatch.setattr(MainWindow, 'start_updates', lambda self: setattr(self, '_updates_started', True))
    ui_root.ready = False
    ui_root.main_window = None
    ui_root.geometry('1360x720')
    ui_root.deiconify()
    callbacks = []
    ui_root.report_callback_exception = lambda *error: callbacks.append(error)
    coordinator = startup.ApplicationStartup(ui_root)
    try:
        assert coordinator.screen.winfo_manager() == 'place'
        if early_stage == 'imports':
            coordinator.enter()
        elif early_stage == 'shell':
            wait(ui_root, lambda: coordinator.shell_task is not None)
            coordinator.enter()
        elif early_stage == 'module':
            wait(ui_root, lambda: coordinator.preloader is not None and bool(coordinator.preloader.partials))
            coordinator.enter()
        wait(ui_root, lambda: ui_root.ready)
        window, loader = ui_root.main_window, coordinator.preloader
        assert window._active_view is window._home and window._active_view_key is None
        assert window._updates_started
        assert not loader.errors
        assert window.frames['ocr'] is None and window.frames['remove_bg'] is None
        assert not coordinator.screen.winfo_manager()
        if early_stage == 'complete':
            assert len([frame for frame in window.frames.values() if frame is not None]) == 9
            assert coordinator.screen.progress.get() == 1
            metadata = window.frames['metadata']
            assert metadata._collection.worker is None
            assert not any(pane.photo for pane in metadata._previews)
            assert window.frames['lqip']._source_job is None
        else:
            assert not loader.running
        # Cambia la selección antes de terminar el build asíncrono: solo vale la más reciente.
        window.show_module('metadata')
        window.show_module('lqip')
        wait(ui_root, lambda: window.frames['lqip'] is not None)
        assert window._active_view is window.frames['lqip']
        window.show_module('metadata')
        wait(ui_root, lambda: window.frames['metadata'] is not None)
        metadata = window.frames['metadata']
        for label in (t('edit'), t('clean_batch'), t('view')):
            metadata._cambiar_tab(label)
            ui_root.update()
        window.show_home()
        window.show_module('metadata')
        assert window._active_view is metadata
        if early_stage == 'complete':
            from PIL import Image
            path = tmp_path / 'startup-photo.jpg'
            Image.new('RGB', (320, 180), 'teal').save(path)
            metadata._cargar_lote([str(path)])
            wait(ui_root, lambda: metadata._preview_ver.photo is not None)
            assert metadata._state.current.path == str(path)
            window.show_module('lqip')
            lqip = window.frames['lqip']
            lqip._cargar_imagenes([str(path)])
            wait(ui_root, lambda: bool(lqip._sources))
            lqip._procesar()
            wait(ui_root, lambda: bool(lqip._results) and not lqip._busy)
            assert lqip._results[0].dimensions == (20, 11)
            lqip._limpiar()
            assert not lqip._results and not lqip._imagenes
        assert not callbacks
    finally:
        coordinator.close()
        if ui_root.main_window:
            ui_root.main_window.destroy()
        coordinator.screen.destroy()


def test_only_visible_modules_are_prepared(ui_root, monkeypatch, tmp_path):
    import json
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'visible_modules': ['convert', 'ocr', 'remove_bg']}))
    monkeypatch.setattr(module_registry, 'settings_path', lambda: path)
    content = ctk.CTkFrame(ui_root)
    window = SimpleNamespace(winfo_toplevel=lambda: ui_root, content=content)
    loader = startup.ModulePreloader(window, PendingImports(), lambda *_: None, lambda: None)
    assert [spec.key for spec in loader.specs] == ['convert', 'settings']


def test_startup_strings_exist_in_all_nine_languages():
    assert len(AVAILABLE_LANGUAGES) == 9
    for module in ('es', 'en', 'de', 'fr', 'it', 'pt', 'ru', 'ja', 'zh_cn'):
        translations = importlib.import_module(f'app.translations.{module}')
        strings = next(value for value in vars(translations).values()
                       if isinstance(value, dict) and 'app_title' in value)
        for key in ('startup_resources', 'startup_home', 'startup_module', 'startup_enter',
                    'startup_error', 'startup_module_error', 'startup_partial'):
            assert strings[key].strip()
        assert '{module}' in strings['startup_module']
        assert '{modules}' in strings['startup_partial']
