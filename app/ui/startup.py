"""Startup screen and resumable UI preload; workers never own Tk objects."""
from __future__ import annotations

from importlib import import_module
import logging
from queue import Empty, Queue, SimpleQueue
from threading import Event, Thread
from time import perf_counter

import customtkinter as ctk
from PIL import Image

from app.translations import t
from app.ui import colors, fonts
from app.ui.building import BuildTask
from app.ui.module_registry import get_module_spec, iter_enabled_modules
from app.ui.rendering import StableRender
from app.utils.paths import resource_path

logger = logging.getLogger(__name__)


class LoadingScreen(ctk.CTkFrame):
    def __init__(self, parent, enter):
        super().__init__(parent, fg_color=colors.FRAMES_BG, corner_radius=0)
        card = ctk.CTkFrame(self, fg_color='transparent')
        card.place(relx=.5, rely=.5, anchor='center')
        card.grid_columnconfigure(0, weight=1)
        try:
            with Image.open(resource_path('assets/icon.png')) as source:
                logo = source.convert('RGBA')
            logo.thumbnail((135, 135))
            self.logo = ctk.CTkImage(light_image=logo, dark_image=logo, size=logo.size)
        except OSError:
            self.logo = None
        ctk.CTkLabel(card, image=self.logo, text='' if self.logo else 'Yagua',
                     font=fonts.FUENTE_TITULO).grid(row=0, column=0, pady=(0, 24))
        self.status = ctk.CTkLabel(card, text=t('startup_resources'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, width=360, wraplength=360, justify='center')
        self.status.grid(row=1, column=0, pady=(0, 14), sticky='ew')
        self.progress = ctk.CTkProgressBar(card, width=360, height=6,
            fg_color=colors.SIDEBAR_SEPARATOR, progress_color=colors.ACENTO)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, sticky='ew')
        self.button = ctk.CTkButton(card, text=t('startup_enter'), command=enter,
            height=36, width=160, font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG, hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR, border_width=1, border_color=colors.SIDEBAR_SEPARATOR)
        self.button.grid(row=3, column=0, pady=(24, 0))
        self.place(x=0, y=0, relwidth=1, relheight=1)


def _import_worker(jobs, results, closed):
    while not closed.is_set():
        job = jobs.get()
        if job is None:
            return
        key, path = job
        if closed.is_set():
            return
        try:
            module, name = path.split(':', 1)
            value = getattr(import_module(module), name)
            if key == '__shell__':
                from app.utils.image_utils import init_heif_support
                init_heif_support()
            result = (value, None)
        except Exception as error:
            logger.exception('startup: import failed key=%s', key)
            result = (None, error)
        if not closed.is_set():
            results.put((key, result))


class Imports:
    def __init__(self, owner):
        self.owner = owner
        self.jobs, self.results = Queue(), SimpleQueue()
        self.closed = Event()
        self.pending = {}
        self.job = None
        self.worker = Thread(target=_import_worker,
            args=(self.jobs, self.results, self.closed), daemon=True, name='yagua-ui-imports')
        self.worker.start()

    def request(self, key, path, callback):
        self.pending[key] = callback
        self.jobs.put((key, path))
        if self.job is None:
            self.job = self.owner.after(10, self._poll)

    def _poll(self):
        self.job = None
        if self.closed.is_set():
            return
        try:
            while True:
                key, result = self.results.get_nowait()
                callback = self.pending.pop(key, None)
                if callback:
                    callback(*result)
        except Empty:
            pass
        if self.pending:
            self.job = self.owner.after(10, self._poll)

    def close(self):
        self.closed.set()
        self.jobs.put(None)
        self.pending.clear()
        if self.job is not None:
            self.owner.after_cancel(self.job)
            self.job = None


class ModulePreloader:
    def __init__(self, window, imports, progress, complete):
        self.window, self.owner, self.imports = window, window.winfo_toplevel(), imports
        self.progress, self.complete = progress, complete
        self.specs = [spec for spec in iter_enabled_modules() if spec.preload_ui
                      and spec.key not in ('ocr', 'remove_bg')]
        self.cursor = 0
        self.running = False
        self.closed = False
        self.current = None
        self.classes, self.tasks, self.partials, self.warmers = {}, {}, {}, {}
        self.loading = set()
        self.errors = {}
        self.listeners = {}
        self.wanted = None

    def start(self):
        if self.closed:
            return
        self.running = True
        self._next()

    def _next(self):
        if not self.running or self.closed:
            return
        if self.cursor == len(self.specs):
            self.running = False
            self.complete()
            return
        spec = self.specs[self.cursor]
        self.current = spec.key
        self.progress(self.cursor, len(self.specs), t(spec.label_key))
        self.ensure(spec.key)

    def pause(self):
        self.running = False
        self.wanted = None
        for task in self.tasks.values():
            task.pause()
        for renderer in self.warmers.values():
            renderer.set_visible(False)
        for frame in self.partials.values():
            self.window._get_view_host(frame).place_forget()

    def ensure(self, key, ready=None, failed=None):
        if self.closed:
            return
        if ready is not None:
            self.listeners[key] = (ready, failed)
        self.wanted = key
        for other, task in self.tasks.items():
            if other != key:
                task.pause()
        for other, renderer in self.warmers.items():
            if other != key and other in self.partials:
                renderer.set_visible(False)
        for other, frame in self.partials.items():
            if other != key:
                self.window._get_view_host(frame).place_forget()
        if self.window.frames.get(key) is not None:
            self._notify(key)
        elif key in self.partials:
            frame = self.partials[key]
            if frame.build_ready:
                self._warm(key)
            else:
                self._place_partial(frame)
                self.tasks[key].resume()
        elif key in self.classes:
            self._construct(key)
        elif key not in self.loading:
            spec = get_module_spec(key)
            if spec is None or not spec.preload_ui or key in ('ocr', 'remove_bg'):
                raise ValueError('Only non-AI UI modules can be preloaded')
            self.loading.add(key)
            self.imports.request(key, spec.frame_import,
                                 lambda cls, error: self._imported(key, cls, error))

    def _imported(self, key, cls, error):
        self.loading.discard(key)
        if self.closed:
            return
        if error is not None:
            self._failed(key, error)
            return
        self.classes[key] = cls
        if self.wanted == key:
            self._construct(key)

    def _construct(self, key):
        previous = set(self.window.content.winfo_children())
        try:
            frame = self.classes[key](self.window.content, defer_build=True)
            self.partials[key] = frame
            self._place_partial(frame)
            self.tasks[key] = BuildTask(self.owner, frame._build_iterator,
                lambda: self._warm(key), lambda error: self._failed(key, error))
            self.tasks[key].resume()
        except Exception as error:
            self._failed(key, error)
            # A constructor can fail before returning its scrollable wrapper.
            for child in set(self.window.content.winfo_children()) - previous:
                if child.winfo_exists():
                    child.destroy()

    def _place_partial(self, frame):
        self.window._get_view_host(frame).place(x=0, y=0, relwidth=1, relheight=1)
        if hasattr(self.window, '_loading_view'):
            self.window._get_view_host(self.window._loading_view).lift()

    def _warm(self, key):
        if self.closed or self.wanted != key:
            return
        frame = self.partials[key]
        self.window._notify_view_hidden(frame)
        host = self.window._get_view_host(frame)
        host.place(x=0, y=0, relwidth=1, relheight=1)
        if hasattr(self.window, '_loading_view'):
            self.window._get_view_host(self.window._loading_view).lift()
        if key not in self.warmers:
            self.warmers[key] = StableRender(self.owner, host, lambda _size: self._ready(key))
        self.warmers[key].set_visible(True)

    def _ready(self, key):
        if self.closed or self.wanted != key:
            return
        frame = self.partials.pop(key)
        self.warmers[key].set_visible(False)
        self.window._get_view_host(frame).place_forget()
        self.window.frames[key] = frame
        self.errors.pop(key, None)
        logger.info('startup: ready module=%s max_step_ms=%.2f max_batch_ms=%.2f', key,
                    self.tasks[key].max_step_ms, self.tasks[key].max_batch_ms)
        self._notify(key)

    def _notify(self, key):
        listener = self.listeners.pop(key, None)
        if listener and listener[0]:
            listener[0](self.window.frames[key])
        if self.running and self.current == key:
            self.cursor += 1
            self.owner.after(1, self._next)

    def _failed(self, key, error):
        logger.error('startup: module failed key=%s error=%s', key, error,
                     exc_info=(type(error), error, error.__traceback__))
        self.errors[key] = str(error)
        task = self.tasks.pop(key, None)
        if task:
            task.cancel()
        renderer = self.warmers.pop(key, None)
        if renderer:
            renderer.set_visible(False)
        frame = self.partials.pop(key, None)
        if frame is not None:
            host = self.window._get_view_host(frame)
            frame.destroy()
            if host.winfo_exists():
                host.destroy()
        listener = self.listeners.pop(key, None)
        if listener and listener[1]:
            listener[1](error)
        if self.running and self.current == key:
            self.cursor += 1
            self.owner.after(1, self._next)

    def close(self):
        self.closed = True
        self.pause()
        for task in self.tasks.values():
            task.cancel()
        self.listeners.clear()


class ApplicationStartup:
    def __init__(self, app):
        self.app = app
        self.started = perf_counter()
        self.imports = Imports(app)
        self.shell_task = None
        self.preloader = None
        self.entered_early = False
        self.closed = False
        self.screen = LoadingScreen(app, self.enter)
        self.screen.lift()
        app.after(16, self.start)

    def start(self):
        if not self.closed:
            self.imports.request('__shell__', 'app.ui.main_window:MainWindow', self._shell_imported)

    def enter(self):
        self.entered_early = True
        self.screen.button.configure(state='disabled')
        if self.preloader:
            self.preloader.pause()
            self.finish()
        else:
            self.screen.status.configure(text=t('startup_home'))

    def _shell_imported(self, cls, error):
        if self.closed:
            return
        if error:
            self._fatal(error)
            return
        self.screen.status.configure(text=t('startup_home'))
        try:
            window = cls(self.app, defer_build=True, auto_updates=False)
            self.app.main_window = window
            window.pack(fill='both', expand=True)
            self.screen.lift()
            self.shell_task = BuildTask(self.app, window._build_iterator, self._shell_ready, self._fatal)
            self.shell_task.resume()
        except Exception as error:
            self._fatal(error)

    def _shell_ready(self):
        if self.closed:
            return
        self.preloader = ModulePreloader(self.app.main_window, self.imports, self._progress, self.finish)
        self.app.main_window._preloader = self.preloader
        if self.entered_early:
            self.finish()
        else:
            self.preloader.start()

    def _progress(self, complete, total, label):
        self.screen.status.configure(text=t('startup_module').format(module=label))
        self.screen.progress.set((complete + 2) / (total + 2))

    def finish(self):
        if self.closed or self.app.ready:
            return
        self.screen.progress.set(1)
        self.screen.place_forget()
        self.app.ready = True
        self.app.main_window.show_home()
        self.app.main_window.start_updates()
        if self.preloader and self.preloader.errors:
            labels = ', '.join(t(spec.label_key) for key in self.preloader.errors
                               if (spec := get_module_spec(key)) is not None)
            self.app.main_window.show_preload_errors(labels)
        logger.info('startup: interactive elapsed_ms=%.2f early=%s',
                    (perf_counter() - self.started) * 1000, self.entered_early)

    def _fatal(self, error):
        if self.closed:
            return
        logger.error('startup: shell failed: %s', error,
                     exc_info=(type(error), error, error.__traceback__))
        from tkinter import messagebox
        messagebox.showerror(t('app_title'), t('startup_error'), parent=self.app)
        self.app.destroy()

    def close(self):
        self.closed = True
        self.imports.close()
        if self.shell_task:
            self.shell_task.cancel()
        if self.preloader:
            self.preloader.close()
