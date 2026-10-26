from types import SimpleNamespace

import pytest

from app.ui import main_window
from app.ui.frames.settings.tabs import updates_tab
from app.utils import update_checker


def _control_threads(monkeypatch, module):
    workers = []

    def thread(*, target, daemon):
        assert daemon
        return SimpleNamespace(start=lambda: workers.append(target))

    monkeypatch.setattr(module.threading, 'Thread', thread)
    return workers


@pytest.mark.parametrize('outcome', ['offline', 'invalid-response', 'no-update', 'prerelease', 'stable'])
def test_update_check_delivers_correct_status_and_restores_controls(ui_root, monkeypatch, outcome):
    tab = updates_tab.UpdatesTab(ui_root)
    workers = _control_threads(monkeypatch, updates_tab)
    callbacks = []
    monkeypatch.setattr(tab, '_post_ui', lambda delay, callback: callbacks.append(callback))
    monkeypatch.setattr(updates_tab, '__version__', '2.0.0')
    monkeypatch.setattr(update_checker, 'get_update_platform', lambda: 'windows')
    state = {'outcome': outcome}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            if state['outcome'] == 'invalid-response':
                return {'invalid': 'payload'}
            if state['outcome'] == 'no-update':
                return []
            if state['outcome'] == 'prerelease':
                return [{'tag_name': 'win-v2.0.1-rc.7', 'prerelease': True,
                         'html_url': 'https://example/rc7'}]
            return [{'tag_name': 'win-v2.0.1', 'prerelease': False,
                     'html_url': 'https://example/stable'}]

    def get(*args, **kwargs):
        if state['outcome'] == 'offline':
            raise update_checker.requests.Timeout('offline')
        return Response()

    monkeypatch.setattr(update_checker.requests, 'get', get)
    tab._mostrar_descarga('old', 'https://example/old')
    tab._check_updates()
    tab._check_updates()
    assert len(workers) == 1  # Double click cannot start another request.
    assert tab._worker_activo
    assert tab._btn_check_updates.cget('state') == 'disabled'
    assert tab._download_url is None
    workers.pop()()
    assert tab._lbl_update_status.cget('text') == updates_tab.t('updates_checking')
    for callback in callbacks:
        callback()
    callbacks.clear()
    assert not tab._worker_activo
    assert tab._btn_check_updates.cget('state') == 'normal'
    if outcome == 'stable':
        assert tab._download_url == 'https://example/stable'
        assert tab._lbl_update_status.cget('text') == updates_tab.t('updates_available').format(version='2.0.1')
    else:
        key = 'no_updates' if outcome in {'no-update', 'prerelease'} else 'updates_error'
        assert tab._lbl_update_status.cget('text') == updates_tab.t(key)
        assert tab._download_url is None
        assert tab._btn_download.winfo_manager() == ''
    if outcome in {'offline', 'invalid-response'}:
        state['outcome'] = 'stable'
        tab._check_updates()
        workers.pop()()
        for callback in callbacks:
            callback()
        assert tab._download_url == 'https://example/stable'
        assert not tab._worker_activo


@pytest.mark.parametrize('outcome', ['error', 'no-update', 'stable'])
def test_startup_update_check_is_nonblocking_and_handles_errors(monkeypatch, outcome):
    workers = _control_threads(monkeypatch, main_window)
    callbacks = []
    banners = []
    owner = SimpleNamespace(_show_update_banner=lambda *args: banners.append(args))
    monkeypatch.setattr(main_window.operations, 'post', lambda widget, callback: callbacks.append(callback))

    def check(version):
        if outcome == 'error':
            raise update_checker.UpdateCheckError('offline')
        if outcome == 'no-update':
            return None
        return update_checker.UpdateInfo('2.0.1', 'https://example/stable')

    monkeypatch.setattr(main_window, 'check_latest_update', check)
    main_window.MainWindow._check_updates_on_startup(owner)
    workers.pop()()
    assert not banners
    for callback in callbacks:
        callback()
    assert banners == ([('2.0.1', 'https://example/stable')] if outcome == 'stable' else [])
