import urllib.error

import pytest

from scripts.ci import checkpoints, preflight


def test_version_and_installer_mismatch_fail_before_build(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight, 'check_source_version', lambda _: None)
    file = tmp_path / 'Yagua.iss'
    file.write_text('AppVersion=2.0.0\nOutputBaseFilename=Yagua_Setup_2.0.0\n')
    preflight.check_version('2.0.0', 'windows', tmp_path)
    file.write_text('AppVersion=2.0.0\nOutputBaseFilename=Yagua_Setup_1.0.0\n')
    with pytest.raises(ValueError, match='filename'):
        preflight.check_version('2.0.0', 'windows', tmp_path)
    with pytest.raises(ValueError, match='Invalid candidate'):
        preflight.check_version('../../output', 'windows', tmp_path)


def test_linux_rebuild_keeps_existing_public_version_guard(monkeypatch):
    monkeypatch.setattr(preflight, 'check_source_version', lambda _: None)
    monkeypatch.setattr(checkpoints, 'api', lambda _: {'id': 123})
    with pytest.raises(ValueError, match='already has'):
        preflight.check_version('2.0.0', 'linux')


def test_linux_unpublished_version_allows_build_and_does_not_ignore_auth_errors(monkeypatch):
    monkeypatch.setattr(preflight, 'check_source_version', lambda _: None)
    def missing(_):
        raise urllib.error.HTTPError('https://github', 404, 'Not Found', {}, None)
    monkeypatch.setattr(checkpoints, 'api', missing)
    preflight.check_version('2.0.0', 'linux')
    def forbidden(_):
        raise RuntimeError('Actions request refused')
    monkeypatch.setattr(checkpoints, 'api', forbidden)
    with pytest.raises(RuntimeError, match='refused'):
        preflight.check_version('2.0.0', 'linux')
