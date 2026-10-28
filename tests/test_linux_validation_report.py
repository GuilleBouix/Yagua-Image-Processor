"""Pruebas de regresión para linux validation report y sus contratos asociados."""

import json

import pytest

from scripts.ci import linux_validation_report
from scripts.ci.check_linux_size import MAX_BYTES
from scripts.ci.extract_release_notes import _extract_section


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_release_notes_include_only_the_requested_version(newline):
    changelog = newline.join([
        '# Changelog', '', '## [2.0.1-rc.5] - 2026-10-15', '',
        'New release changes.', '', '## [2.0.0] - 2026-04-09', '', 'Old changes.', '',
    ])
    assert _extract_section(changelog, '2.0.1-rc.5') == 'New release changes.'
    assert _extract_section(changelog, '2.0.0') == 'Old changes.'
    assert _extract_section(changelog, 'missing') is None


@pytest.mark.parametrize('installed_bytes', [1_527_547_175, MAX_BYTES])
def test_linux_release_report_keeps_changes_and_enforces_installed_limit(tmp_path, monkeypatch, installed_bytes):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(linux_validation_report, 'ROOT', tmp_path)
    for name, value in {
        'RELEASE_VERSION': '2.0.1-rc.5', 'GITHUB_SHA': 'tested-commit',
        'GITHUB_REPOSITORY': 'owner/yagua', 'GITHUB_RUN_ID': '123',
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    (tmp_path / 'CHANGELOG.md').write_text('## [2.0.1-rc.5] - 2026-10-15\n\nRelease changes.\n')
    reports = tmp_path / 'reports'
    reports.mkdir()
    fixtures = {
        'selftest-preflight.json': {'status': 'passed', 'mode': 'preflight'},
        'selftest-appimage-runtime.json': {'status': 'passed', 'restart_uses_appimage': True},
        'selftest-online.json': {'status': 'passed', 'frozen': True},
        'selftest-offline.json': {'status': 'passed', 'frozen': True, 'offline': True},
        'installed-size.json': {'within_budget': installed_bytes < MAX_BYTES, 'installed_bytes': installed_bytes},
    }
    for name, data in fixtures.items():
        (reports / name).write_text(json.dumps(data))
    distribution = tmp_path / 'dist/linux-release'
    distribution.mkdir(parents=True)
    (distribution / 'sizes.json').write_text(json.dumps({'artifacts': [{'path': 'Yagua.AppImage', 'bytes': 123}]}))
    if installed_bytes >= MAX_BYTES:
        with pytest.raises(AssertionError):
            linux_validation_report.main()
        assert not (reports / 'validation.md').exists()
    else:
        linux_validation_report.main()
        content = (reports / 'validation.md').read_text()
        assert 'Release changes.' in content
        assert 'Commit: tested-commit' in content
        assert 'network access blocked' in content
        assert f'strictly below {MAX_BYTES:,}' in content
