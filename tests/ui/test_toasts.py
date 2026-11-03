"""Real Tk lifecycle of the two floating notices, without model downloads or releases."""
from time import monotonic, sleep

import customtkinter as ctk
import pytest

from app.ui import colors, fonts, main_window
from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.operations import operations
from app.ui.toast import Toast
from app.utils.update_checker import UpdateInfo


def wait(root, condition, timeout=5):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        root.update()
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        if condition():
            return
        sleep(.005)
    raise AssertionError('Notice did not reach the expected state')


def settled(root, *widgets):
    previous = None
    since = monotonic()

    def stable():
        nonlocal previous, since
        geometry = tuple((w.winfo_x(), w.winfo_y(), w.winfo_width(), w.winfo_height()) for w in widgets)
        if any(width <= 1 or height <= 1 for _, _, width, height in geometry):
            return False
        if geometry != previous:
            previous, since = geometry, monotonic()
            return False
        return monotonic() - since >= .032

    wait(root, stable)


@pytest.fixture(autouse=True)
def isolate(ui_root, monkeypatch):
    """Aísla el gestor de avisos flotantes entre casos de UI."""
    if fonts.FUENTE_BASE is None:
        fonts.inicializar_fuentes()
    old_theme, old_scale = colors.get_current_theme(), ctk.ScalingTracker.widget_scaling
    tracker = ctk.ScalingTracker
    callbacks = {window: list(items) for window, items in tracker.window_widgets_dict.items()}
    dpi_scaling = dict(tracker.window_dpi_scaling_dict)
    errors = []
    monkeypatch.setattr(ui_root._root(), 'report_callback_exception',
                        lambda kind, error, tb: errors.append(f'{kind.__name__}: {error}'))
    yield
    for child in list(ui_root.winfo_children()):
        child.destroy()
    ui_root.update_idletasks()
    assert not any(isinstance(getattr(callback, '__self__', None), Toast)
                   for items in tracker.window_widgets_dict.values() for callback in items)
    # Match the project's isolated-window fixtures: native CTk dropdown menus
    # retain callbacks until their toplevel closes. Do not scale destroyed menus.
    tracker.window_widgets_dict = callbacks
    tracker.window_dpi_scaling_dict = dpi_scaling
    tracker.widget_scaling = old_scale
    colors.apply_theme(old_theme)
    ui_root.update()
    assert not errors


@pytest.mark.parametrize('theme', colors.get_theme_names()[:2])
@pytest.mark.parametrize('geometry', ['1400x900', '900x600'])
@pytest.mark.parametrize('scale', [1, .75, .5])
def test_notices_fit_stack_resize_and_release_bindings(ui_root, theme, geometry, scale):
    colors.apply_theme(theme)
    ctk.set_widget_scaling(scale)
    ui_root.geometry(geometry)
    ui_root.deiconify()
    host = ctk.CTkFrame(ui_root)
    host.pack(fill='both', expand=True)
    sentinel = host.bind('<Configure>', lambda event: None, add='+')
    original_bindings = host.bind('<Configure>')
    first = Toast(host, 'New stable version available', action_text='Download', action=lambda: None)
    second = Toast(host, 'The model will download automatically when processing. ' * 3)
    settled(ui_root, host, first, second)
    for notice in (first, second):
        assert notice.winfo_width() <= 380 * notice._get_widget_scaling() + 1
        assert abs(host.winfo_width() - notice.winfo_x() - notice.winfo_width() - 16 * notice._get_widget_scaling()) <= 2
    assert second.winfo_y() >= first.winfo_y() + first.winfo_height() + 11 * second._get_widget_scaling()
    ctk.set_widget_scaling(.75 if scale == 1 else 1)
    settled(ui_root, host, first, second)
    assert first.winfo_width() <= 380 * first._get_widget_scaling() + 1
    assert second.winfo_y() >= first.winfo_y() + first.winfo_height() + 11 * second._get_widget_scaling()
    before = host.winfo_width(), host.winfo_height()
    first.close_button.invoke()
    settled(ui_root, host, second)
    assert not first.winfo_exists()
    assert abs(second.winfo_y() - 16 * second._get_widget_scaling()) <= 1
    assert (host.winfo_width(), host.winfo_height()) == before
    # A narrow central area must wrap the text and keep both edges inside it.
    ui_root.geometry('300x600')
    settled(ui_root, host, second)
    assert second.winfo_x() >= 0
    assert second.winfo_x() + second.winfo_width() <= host.winfo_width()
    second.close_button.invoke()
    assert host.bind('<Configure>') == original_bindings
    host.unbind('<Configure>', sentinel)


def shell(root):
    root.geometry('1000x700')
    root.deiconify()
    window = main_window.MainWindow(root, auto_updates=False)
    window.pack(fill='both', expand=True)
    settled(root, window, window.content)
    return window


@pytest.mark.parametrize('available', [False, True])
def test_actual_update_delivery_action_dedup_navigation_and_close(ui_root, monkeypatch, available):
    window = shell(ui_root)
    assert getattr(window, '_update_banner', None) is None  # No forced preview at startup.
    workers = []

    class Worker:
        """Worker controlable para reproducir resultados sin depender del reloj real."""
        def __init__(self, *, target, daemon):
            self.target = target

        def start(self):
            workers.append(self.target)

    monkeypatch.setattr(main_window.threading, 'Thread', Worker)
    monkeypatch.setattr(main_window, 'check_latest_update', lambda version:
                        UpdateInfo('9.0.0', 'https://example.test/stable') if available else None)
    opened = []
    monkeypatch.setattr(main_window.webbrowser, 'open', lambda url: opened.append(url))
    window._check_updates_on_startup()
    workers.pop()()
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    if not available:
        assert getattr(window, '_update_banner', None) is None
        return
    notice = window._update_banner
    assert isinstance(notice, Toast)
    settled(ui_root, notice)
    window._show_update_banner('9.0.0', 'https://example.test/stable')
    assert [child for child in window.content.winfo_children() if isinstance(child, Toast)] == [notice]
    notice.action_button.invoke()
    assert opened == ['https://example.test/stable']
    window.show_module('compress')
    settled(ui_root, notice)
    assert notice.winfo_ismapped()
    assert window.content.winfo_children()[-1] is notice
    old_timer = window._update_banner_job
    notice.close_button.invoke()
    assert not notice.winfo_exists() and window._update_banner is None
    assert window._update_banner_job is None
    assert old_timer not in ui_root.tk.call('after', 'info')
    window._hide_update_banner()  # Repeated close is harmless.
    window._show_update_banner('9.0.0', 'https://example.test/stable')
    assert window._update_banner.winfo_exists()
    timed_notice = window._update_banner
    started = monotonic()
    wait(ui_root, lambda: window._update_banner is None, timeout=11.5)
    assert monotonic() - started >= 9.5
    assert not timed_notice.winfo_exists() and window._update_banner_job is None
    window._show_update_banner('9.0.0', 'https://example.test/stable')
    window.destroy()
    ui_root.update()


def removal(window, root, monkeypatch, *, cached=False):
    monkeypatch.setattr(RemoveBgFrame, '_inicializar_en_background',
                        lambda self: self._build_content_ready(True, cached))
    frame = RemoveBgFrame(window.content)
    window.frames['remove_bg'] = frame
    window._show_view(frame, 'remove_bg')
    wait(root, lambda: hasattr(frame, '_btn_seleccionar'))
    return frame


def test_first_download_expires_after_five_seconds_without_forced_display(ui_root, monkeypatch):
    window = shell(ui_root)
    frame = removal(window, ui_root, monkeypatch)
    notice = frame._primer_uso_notice
    assert isinstance(notice, Toast)
    assert notice.master is window.content
    started = monotonic()
    wait(ui_root, lambda: frame._primer_uso_notice is None, timeout=6.5)
    assert monotonic() - started >= 4.5
    assert not notice.winfo_exists()
    assert frame._primer_uso_notice_job is None


def test_cached_model_has_no_notice_and_close_navigation_cancel_timers(ui_root, monkeypatch):
    window = shell(ui_root)
    frame = removal(window, ui_root, monkeypatch, cached=True)
    assert frame._primer_uso_notice is None
    window._show_update_banner('9.0.0', 'https://example.test/stable')
    update = window._update_banner
    frame._construir_aviso_primer_uso()
    old_timer = frame._primer_uso_notice_job
    frame._primer_uso_notice.close_button.invoke()
    assert frame._primer_uso_notice is None and frame._primer_uso_notice_job is None
    assert old_timer not in ui_root.tk.call('after', 'info')
    assert update.winfo_exists()
    frame._construir_aviso_primer_uso()
    first = frame._primer_uso_notice
    frame._construir_aviso_primer_uso()
    assert not first.winfo_exists()
    assert len([child for child in window.content.winfo_children() if isinstance(child, Toast)]) == 2
    settled(ui_root, update, frame._primer_uso_notice)
    window.show_home()
    assert frame._primer_uso_notice is None and frame._primer_uso_notice_job is None
    assert update.winfo_exists()
    window._show_view(frame, 'remove_bg')
    assert frame._primer_uso_notice is None  # Navigation cannot revive the expired/closed notice.
    frame._construir_aviso_primer_uso()
    window.destroy()  # Also closes an active notice owned outside the module.
    ui_root.update()
