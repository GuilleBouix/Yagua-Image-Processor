"""Reject distribution artifacts at or above the installed 2 GB ceiling.

This preliminary artifact check does not certify the installed total. Use
check_installed_size.py after the online/offline model checks for that gate.
"""
# Valida el límite de tamaño instalado de los paquetes Linux.

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat

MAX_BYTES = 2_000_000_000


def artifact_size(path: Path) -> int:
    """Count regular files without following symlinks."""
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path, followlinks=False):
        for name in files:
            info = (Path(root) / name).lstat()
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
    return total


def within_budget(size: int) -> bool:
    """Comprueba el presupuesto instalado sin crear archivos gigantes."""
    return 0 <= size < MAX_BYTES


def main(argv: list[str] | None = None) -> int:
    """Valida el tamaño del artefacto Linux y su informe de mediciones."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    artifacts = [{'path': str(path), 'bytes': artifact_size(path)} for path in args.paths]
    report = {'limit_bytes': MAX_BYTES, 'artifacts': artifacts}
    encoded = json.dumps(report, indent=2)
    print(encoded)
    if args.report:
        args.report.write_text(encoded + '\n', encoding='utf-8')
    if not all(within_budget(item['bytes']) for item in artifacts):
        parser.exit(1, f'ERROR: un artefacto alcanza o supera {MAX_BYTES:,} bytes.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
