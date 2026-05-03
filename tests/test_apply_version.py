from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "apply_version.py"
SPEC = importlib.util.spec_from_file_location("apply_version_script", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
apply_version = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apply_version)


def test_apply_version_main_linux_no_toca_inno(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setattr(apply_version, "_apply_app_version_py", lambda root, version: calls.append(("app", root, version)))
    monkeypatch.setattr(apply_version, "_apply_inno_iss", lambda root, version: calls.append(("inno", root, version)))
    monkeypatch.setattr(apply_version.Path, "resolve", lambda self: tmp_path / "scripts" / "ci" / "apply_version.py")

    rc = apply_version.main(["apply_version.py", "2.1.0", "linux"])

    assert rc == 0
    assert calls == [("app", tmp_path, "2.1.0")]


def test_apply_version_main_windows_toca_inno(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setattr(apply_version, "_apply_app_version_py", lambda root, version: calls.append(("app", root, version)))
    monkeypatch.setattr(apply_version, "_apply_inno_iss", lambda root, version: calls.append(("inno", root, version)))
    monkeypatch.setattr(apply_version.Path, "resolve", lambda self: tmp_path / "scripts" / "ci" / "apply_version.py")

    rc = apply_version.main(["apply_version.py", "2.1.0", "windows"])

    assert rc == 0
    assert calls == [
        ("app", tmp_path, "2.1.0"),
        ("inno", tmp_path, "2.1.0"),
    ]


def test_apply_version_rechaza_target_invalido():
    rc = apply_version.main(["apply_version.py", "2.1.0", "macos"])
    assert rc == 2
