import re
import io

import pytest

from app.utils import package_selftest


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
