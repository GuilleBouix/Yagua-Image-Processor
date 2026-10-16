from __future__ import annotations

import pytest

from app.utils import update_checker


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_check_latest_update_filtra_por_windows(monkeypatch):
    payload = [
        {"tag_name": "linux-v9.9.9", "prerelease": False, "draft": False, "html_url": "https://example/linux"},
        {"tag_name": "win-v2.1.0", "prerelease": False, "draft": False, "html_url": "https://example/win-210"},
        {"tag_name": "win-v2.0.5", "prerelease": False, "draft": False, "html_url": "https://example/win-205"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "windows")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_update("2.0.0")

    assert info is not None
    assert info.version == "2.1.0"
    assert info.release_url == "https://example/win-210"


def test_check_latest_update_filtra_por_linux(monkeypatch):
    payload = [
        {"tag_name": "win-v3.0.0", "prerelease": False, "draft": False, "html_url": "https://example/win"},
        {"tag_name": "linux-v2.5.0", "prerelease": False, "draft": False, "html_url": "https://example/linux-250"},
        {"tag_name": "linux-v2.4.9", "prerelease": False, "draft": False, "html_url": "https://example/linux-249"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "linux")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_update("2.4.0")

    assert info is not None
    assert info.version == "2.5.0"
    assert info.release_url == "https://example/linux-250"


def test_check_latest_update_incluye_prerelease_y_excluye_draft(monkeypatch):
    payload = [
        {"tag_name": "linux-v3.0.0-rc.1", "prerelease": True, "draft": False, "html_url": "https://example/rc"},
        {"tag_name": "linux-v3.0.0", "prerelease": False, "draft": True, "html_url": "https://example/draft"},
        {"tag_name": "linux-v2.0.0", "prerelease": False, "draft": False, "html_url": "https://example/stable"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "linux")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    info = update_checker.check_latest_update("1.9.0")

    assert info is not None
    assert info.version == "3.0.0-rc.1"
    assert info.release_url == "https://example/rc"


def test_check_latest_update_devuelve_none_si_no_hay_release_superior(monkeypatch):
    payload = [
        {"tag_name": "win-v2.0.0", "prerelease": False, "draft": False, "html_url": "https://example/win"},
    ]

    monkeypatch.setenv("YAGUA_UPDATE_PLATFORM", "windows")
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    assert update_checker.check_latest_update("2.0.0") is None


def test_check_latest_update_rechaza_payload_no_lista(monkeypatch):
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse({"items": []}))

    with pytest.raises(update_checker.UpdateCheckError):
        update_checker.check_latest_update("2.0.0")


def test_check_latest_update_rechaza_version_actual_invalida(monkeypatch):
    monkeypatch.setattr(update_checker.requests, "get", lambda *args, **kwargs: _FakeResponse([]))

    with pytest.raises(update_checker.UpdateCheckError):
        update_checker.check_latest_update("no-es-version")


def test_check_latest_update_distingue_timeout_de_sin_actualizaciones(monkeypatch):
    def fail_request(*args, **kwargs):
        raise update_checker.requests.Timeout("offline")

    monkeypatch.setattr(update_checker.requests, "get", fail_request)

    with pytest.raises(update_checker.UpdateCheckError) as error:
        update_checker.check_latest_update("2.0.0")
    assert isinstance(error.value.__cause__, update_checker.requests.Timeout)


@pytest.mark.parametrize('url', ['javascript:alert(1)', None, 123, 'https://user:pass@example.com', 'https://[invalid'])
def test_update_url_rejects_non_https_and_non_strings(monkeypatch, url):
    from app.utils import update_checker
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return [{'tag_name': 'win-v9.0.0', 'html_url': url}]
    monkeypatch.setattr(update_checker.requests, 'get', lambda *args, **kwargs: Response())
    monkeypatch.setattr(update_checker, 'get_repo', lambda: 'owner/repo')
    monkeypatch.setattr(update_checker, 'get_update_platform', lambda: 'windows')
    info = update_checker.check_latest_update('2.0.0')
    assert info is not None
    assert info.release_url == 'https://github.com/owner/repo/releases/tag/win-v9.0.0'


@pytest.mark.parametrize('platform', ['windows', 'linux'])
@pytest.mark.parametrize(('current', 'versions', 'expected'), [
    ('2.0.1-rc.4', ['2.0.1-rc.5'], '2.0.1-rc.5'),
    ('2.0.1-rc.4', ['2.0.1-rc.10', '2.0.1-rc.5'], '2.0.1-rc.10'),
    ('2.0.1-rc.5', ['2.0.1-rc.5', '2.0.1-rc.4'], None),
    ('2.0.1-rc.5', ['2.0.1', '2.0.1-rc.10'], '2.0.1'),
    ('2.0.1', ['2.0.1-rc.10', '2.0.2-rc.1'], '2.0.2-rc.1'),
])
def test_prerelease_upgrade_order_and_platform(monkeypatch, platform, current, versions, expected):
    prefix = 'win-v' if platform == 'windows' else 'linux-v'
    other_prefix = 'linux-v' if platform == 'windows' else 'win-v'
    payload = [
        {'tag_name': prefix + version, 'prerelease': '-rc.' in version,
         'html_url': 'https://example/' + version} for version in versions
    ] + [
        {'tag_name': prefix + '99.0.0', 'draft': True},
        {'tag_name': other_prefix + '99.0.0'},
        {'tag_name': prefix + 'invalid'}, None, 42,
    ]
    monkeypatch.setattr(update_checker, 'get_update_platform', lambda: platform)
    monkeypatch.setattr(update_checker.requests, 'get', lambda *args, **kwargs: _FakeResponse(payload))
    info = update_checker.check_latest_update(current)
    if expected is None:
        assert info is None
    else:
        assert info is not None
        assert info.version == expected
        assert info.release_url == 'https://example/' + expected


@pytest.mark.parametrize('failure', ['connection', 'http', 'json'])
def test_network_http_and_invalid_json_are_reported_as_errors(monkeypatch, failure):
    class Response(_FakeResponse):
        def raise_for_status(self):
            if failure == 'http':
                raise update_checker.requests.HTTPError('403 rate limit')

        def json(self):
            if failure == 'json':
                raise ValueError('invalid JSON')
            return super().json()

    def get(*args, **kwargs):
        if failure == 'connection':
            raise update_checker.requests.ConnectionError('offline')
        return Response([])

    monkeypatch.setattr(update_checker.requests, 'get', get)
    with pytest.raises(update_checker.UpdateCheckError):
        update_checker.check_latest_update('2.0.1-rc.4')
