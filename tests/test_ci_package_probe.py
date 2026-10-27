from pathlib import Path

import pytest

from scripts.ci.stages import probe


def test_raw_preflight_uses_original_runtime_instead_of_appimage_rewritten_elf(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, 'PLATFORM', 'linux')
    monkeypatch.setattr(probe, 'ROOT', tmp_path)
    monkeypatch.setattr(probe, 'REPORTS', tmp_path / 'reports')
    monkeypatch.setattr(probe, 'VERSION', '2.0.0')
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path / 'temporary'))
    monkeypatch.setattr(probe, 'system', lambda **_: None)
    runtime = tmp_path / 'dist/linux-release/Yagua/Yagua'
    runtime.parent.mkdir(parents=True)
    runtime.write_bytes(b'original frozen runtime')
    (tmp_path / 'dist/linux-release/Yagua-2.0.0-x86_64.AppImage').write_bytes(b'packaged appimage')
    def extract(*_, cwd, **kwargs):
        # The packaged ELF is not directly executable on its own: AppRun
        # supplies its rewritten loader. It is intentionally absent here.
        (Path(cwd) / 'squashfs-root').mkdir()
    monkeypatch.setattr(probe.subprocess, 'run', extract)
    class PreflightReached(Exception):
        pass
    def preflight(interpreter, script, executable, *args, **kwargs):
        assert executable == runtime
        assert executable.is_file()
        raise PreflightReached
    monkeypatch.setattr(probe, 'xvfb', preflight)
    with pytest.raises(PreflightReached):
        probe.main()
