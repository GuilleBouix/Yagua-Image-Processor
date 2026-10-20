import re
import io
from pathlib import Path

import pytest

from app.utils import package_selftest


def test_startup_probe_waits_for_explicit_readiness(monkeypatch):
    from types import SimpleNamespace
    app = SimpleNamespace(ready=False, winfo_exists=lambda: True,
                          _startup=SimpleNamespace(preloader=SimpleNamespace(errors={})))
    app.update = lambda: setattr(app, 'ready', True)
    monkeypatch.setattr(package_selftest.time, 'sleep', lambda _seconds: None)
    package_selftest._await_startup(app)
    assert app.ready


@pytest.mark.parametrize('state', ['timeout', 'closed', 'module_error'])
def test_startup_probe_reports_failure(state):
    from types import SimpleNamespace
    app = SimpleNamespace(ready=state == 'module_error',
        winfo_exists=lambda: state != 'closed',
        _startup=SimpleNamespace(preloader=SimpleNamespace(errors={'metadata': 'failed'})))
    with pytest.raises((RuntimeError, TimeoutError)):
        package_selftest._await_startup(app, timeout_seconds=0 if state == 'timeout' else 1)


@pytest.mark.parametrize('symbol', ['check_latest_update', 'check_latest_stable'])
def test_package_probe_disables_update_network_for_current_and_baseline_sources(symbol):
    from types import SimpleNamespace

    module = SimpleNamespace(**{symbol: lambda _: None})
    assert package_selftest._update_checker_name(module) == symbol


def test_probe_supports_unicode_in_redirected_windows_console(monkeypatch):
    output = io.BytesIO()
    stream = io.TextIOWrapper(output, encoding='cp1252')
    monkeypatch.setattr(package_selftest.sys, 'stdout', stream)
    package_selftest._prepare_probe_stdio()
    stream.write('█')
    stream.flush()
    assert output.getvalue() == '█'.encode('utf-8')


def test_load_inter_font_reports_missing_resource(monkeypatch, tmp_path):
    missing = tmp_path / 'missing.ttf'
    monkeypatch.setattr(package_selftest, 'resource_path', lambda _: missing)

    with pytest.raises(RuntimeError, match=re.escape(f'Packaged Inter font is missing: {missing}')):
        package_selftest._load_inter_font()


def test_load_inter_font_reports_damaged_resource(monkeypatch, tmp_path):
    damaged = tmp_path / 'damaged.ttf'
    damaged.write_bytes(b'not a font')
    monkeypatch.setattr(package_selftest, 'resource_path', lambda _: damaged)

    with pytest.raises(
        RuntimeError,
        match=re.escape(f'Packaged Inter font cannot be opened: {damaged}'),
    ):
        package_selftest._load_inter_font()


def test_wait_for_ui_reports_timeout():
    class FakeApp:
        def __init__(self):
            self.callbacks = []

        def after(self, _delay, callback):
            self.callbacks.append(callback)

    clock_values = iter((10.0, 41.0))
    app = FakeApp()
    outcomes = []
    package_selftest._wait_for_ui(
        app,
        ready=lambda: False,
        on_ready=lambda: outcomes.append('ready'),
        on_timeout=lambda: outcomes.append('timeout'),
        timeout_seconds=30.0,
        clock=lambda: next(clock_values),
    )

    app.callbacks.pop(0)()

    assert outcomes == ['timeout']
    assert not app.callbacks


def test_conversion_profile_probe_rejects_missing_profile(tmp_path, monkeypatch):
    from PIL import Image

    original_save = Image.Image.save

    def lose_profile(image, destination, format=None, **kwargs):
        if format in ('JPEG', 'WEBP'):
            kwargs.pop('icc_profile', None)
        return original_save(image, destination, format, **kwargs)

    monkeypatch.delenv('YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS', raising=False)
    monkeypatch.setattr(Image.Image, 'save', lose_profile)
    with pytest.raises(RuntimeError, match='lost ICC profile'):
        package_selftest._verify_conversion_profiles(tmp_path)
    monkeypatch.setenv('YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS', '1')
    assert not any(package_selftest._verify_conversion_profiles(tmp_path).values())


def test_conversion_profile_probe_reads_exported_files(tmp_path, monkeypatch):
    monkeypatch.delenv('YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS', raising=False)
    assert package_selftest._verify_conversion_profiles(tmp_path) == {
        'RGB-JPEG': True, 'RGB-WEBP': True, 'RGBA-JPEG': True, 'RGBA-WEBP': True,
    }


def test_frozen_numba_fallback_uses_measured_cache_not_windows_known_folder(tmp_path, monkeypatch):
    from numba.core import caching

    # Restore the third-party module after testing the process-local override.
    monkeypatch.setattr(caching, 'AppDirs', caching.AppDirs)
    monkeypatch.setattr(caching.sys, 'frozen', True, raising=False)
    measured = tmp_path / 'profile/numba'
    package_selftest._redirect_probe_numba_cache(measured)
    nonexistent_source = str(tmp_path / 'frozen-module.py')
    locator = caching.UserWideCacheLocator.from_function(lambda: None, nonexistent_source)
    assert locator is not None
    assert Path(locator.get_cache_path()).is_relative_to(measured)
