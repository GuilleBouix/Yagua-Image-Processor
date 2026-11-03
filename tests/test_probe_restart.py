"""Regression checks for the real packaged settings/restart verification."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import probe_restart


@pytest.mark.parametrize('pid,splash,expected', [(10, False, None), (11, True, None), (11, False, 11)])
def test_home_requires_new_process_and_completed_splash(pid, splash, expected):
    fake_tk = SimpleNamespace(call=lambda *args: pid)
    probe = object.__new__(probe_restart.RestartProbe)
    probe.client = SimpleNamespace(tk=fake_tk)
    probe.before = {'controller'}
    probe.peer = None
    probe.profile_home = None
    probe.peers = lambda: ('controller', 'app')
    probe.wait = lambda check, message: check()
    probe.remote = lambda script: pid if script == 'pid' else None
    probe.find = lambda text: text == probe_restart.TEXT['English'][0] or (
        splash and text == 'Enter now')
    assert probe.home('English', previous_pid=10) == expected


def test_missing_replacement_never_passes_readiness():
    probe = object.__new__(probe_restart.RestartProbe)
    probe.before = {'controller'}
    probe.peer = None
    probe.profile_home = None
    probe.peers = lambda: ('controller',)
    def wait(check, message):
        assert check() is None
        raise TimeoutError(message)
    probe.wait = wait
    with pytest.raises(TimeoutError, match='did not reopen'):
        probe.home('English', previous_pid=10)


def test_peer_name_reuse_is_matched_by_profile_not_initial_name(monkeypatch):
    profile = Path('/tmp/isolated-profile')
    marker = b'HOME=' + os.fsencode(profile) + b'\0'
    class Process:
        """Representa un proceso y su archivo de entorno bajo /proc."""
        def __init__(self, path):
            self.path = path

        def read_bytes(self):
            return marker if self.path == '/proc/11/environ' else b'HOME=/other\0'

    monkeypatch.setattr(probe_restart, 'Path', Process)
    def call(*args):
        if args == ('tk', 'appname'):
            return 'controller'
        return 11 if args[1] == 'reused-name' else 12
    probe = object.__new__(probe_restart.RestartProbe)
    probe.client = SimpleNamespace(tk=SimpleNamespace(call=call))
    probe.profile_home = profile
    probe.before = {'controller', 'reused-name'}
    probe.peers = lambda: ('controller', 'reused-name', 'other-app')
    assert probe.owned_peers() == {'reused-name'}


@pytest.mark.parametrize('state,expected', [('S', False), ('Z', True)])
def test_process_exit_recognizes_zombie_without_waiting_for_reaping(monkeypatch, state, expected):
    process = SimpleNamespace(read_text=lambda: f'123 (Yagua process) {state} 1 2 3')
    monkeypatch.setattr(probe_restart, 'Path', lambda path: process)
    assert probe_restart.process_exited(123) is expected


def test_failed_probe_preserves_report_and_closes_owned_resources(monkeypatch, tmp_path):
    closed = []
    client = SimpleNamespace(withdraw=lambda: None, destroy=lambda: closed.append('client'),
                             tk=SimpleNamespace(call=lambda *args: None))
    monkeypatch.setattr(probe_restart.tk, 'Tk', lambda: client)

    class Probe:
        """Doble de la sonda para reproducir esperas y reinicios de forma controlada."""
        def __init__(self, *args):
            self.client = args[0]

        def home(self, *args):
            raise RuntimeError('Replacement failed')

        def tree(self):
            return []

        def close(self):
            closed.append('windows')

    monkeypatch.setattr(probe_restart, 'RestartProbe', Probe)
    monkeypatch.setattr(probe_restart.subprocess, 'Popen',
                        lambda *args, **kwargs: SimpleNamespace(wait=lambda **kw: 0))
    output = tmp_path / 'reports'
    with pytest.raises(RuntimeError, match='Replacement failed'):
        probe_restart.run(tmp_path / 'Yagua.AppImage', output)
    result = json.loads((output / 'restart.json').read_text())
    assert result['status'] == 'failed' and result['restarts'] == []
    assert 'Replacement failed' in result['error']
    assert closed == ['windows', 'client']


def test_restart_probe_is_wired_to_real_appimage_stage():
    from scripts.ci import checkpoints
    root = Path(__file__).resolve().parents[1]
    stage = (root / 'scripts/ci/stages/probe.py').read_text()
    assert "'scripts/ci/probe_restart.py', compressed" in stage
    files = ['scripts/ci/probe_restart.py']
    assert checkpoints.stage_files('probe', 'linux', files) == files
    assert checkpoints.stage_files('compile', 'linux', files) == []
