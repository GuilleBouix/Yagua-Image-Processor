from __future__ import annotations

from app.utils import update_checker


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_check_latest_stable_filtra_por_windows(monkeypatch):
    payload = [
        {"tag_name": "linux-v9.9.9", "prerelease": False, "draft": False, "html_url": "https://example/linux"},
        {"tag_name": "win-v2.1.0", "prerelease": False, "draft": False, "html_url": "https://example/win-210"},
        {"tag_name": "win-v2.0.5", "prerelease": False, "draft": False, "html_url": "https://example/win-205"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "windows")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_stable("2.0.0")

    assert info is not None
    assert info.version == "2.1.0"
    assert info.release_url == "https://example/win-210"


def test_check_latest_stable_filtra_por_linux(monkeypatch):
    payload = [
        {"tag_name": "win-v3.0.0", "prerelease": False, "draft": False, "html_url": "https://example/win"},
        {"tag_name": "linux-v2.5.0", "prerelease": False, "draft": False, "html_url": "https://example/linux-250"},
        {"tag_name": "linux-v2.4.9", "prerelease": False, "draft": False, "html_url": "https://example/linux-249"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "linux")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_stable("2.4.0")

    assert info is not None
    assert info.version == "2.5.0"
    assert info.release_url == "https://example/linux-250"


def test_check_latest_stable_ignora_prerelease_y_draft(monkeypatch):
    payload = [
        {"tag_name": "linux-v3.0.0-rc.1", "prerelease": True, "draft": False, "html_url": "https://example/rc"},
        {"tag_name": "linux-v3.0.0", "prerelease": False, "draft": True, "html_url": "https://example/draft"},
        {"tag_name": "linux-v2.0.0", "prerelease": False, "draft": False, "html_url": "https://example/stable"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "linux")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_stable("1.9.0")

    assert info is not None
    assert info.version == "2.0.0"
    assert info.release_url == "https://example/stable"


def test_check_latest_stable_devuelve_none_si_no_hay_release_superior(monkeypatch):
    payload = [
        {"tag_name": "win-v2.0.0", "prerelease": False, "draft": False, "html_url": "https://example/win"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "windows")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    assert update_checker.check_latest_stable("2.0.0") is None
