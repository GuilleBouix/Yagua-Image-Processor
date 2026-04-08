from __future__ import annotations

import re
import sys
from pathlib import Path


# Allow semver pre-release tags (e.g. 2.0.0-rc.1) for CI pre-releases.
_VER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?$")


def _replace_line(text: str, pattern: re.Pattern[str], replacement: str) -> str:
    new_text, n = pattern.subn(replacement, text, count=1)
    if n != 1:
        raise RuntimeError(f"No se pudo actualizar: patron={pattern.pattern!r}")
    return new_text


def _apply_app_version_py(repo_root: Path, version: str) -> None:
    path = repo_root / "app" / "version.py"
    text = path.read_text(encoding="utf-8")
    text = _replace_line(
        text,
        re.compile(r'^__version__\s*=\s*".*?"\s*$', re.MULTILINE),
        f'__version__ = "{version}"',
    )
    path.write_text(text, encoding="utf-8")


def _apply_inno_iss(repo_root: Path, version: str) -> None:
    path = repo_root / "Yagua.iss"
    text = path.read_text(encoding="utf-8")
    text = _replace_line(
        text,
        re.compile(r"^AppVersion=.*$", re.MULTILINE),
        f"AppVersion={version}",
    )
    text = _replace_line(
        text,
        re.compile(r"^AppVerName=.*$", re.MULTILINE),
        f"AppVerName=Yagua {version}",
    )
    text = _replace_line(
        text,
        re.compile(r"^OutputBaseFilename=.*$", re.MULTILINE),
        f"OutputBaseFilename=Yagua_Setup_{version}",
    )
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Uso: python scripts/ci/apply_version.py <X.Y.Z>", file=sys.stderr)
        return 2

    version = argv[1].strip()
    if not _VER_RE.match(version):
        print(f"Version invalida: {version!r} (esperado X.Y.Z)", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    _apply_app_version_py(repo_root, version)
    _apply_inno_iss(repo_root, version)
    print(f"OK: version aplicada = {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
