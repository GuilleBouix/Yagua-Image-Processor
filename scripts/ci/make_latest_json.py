"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. make latest json."""

from __future__ import annotations

import json
import sys


def main(argv: list[str]) -> int:
    """Genera el manifiesto de actualización a partir de la versión validada."""
    if len(argv) != 6:
        print(
            "Uso: python scripts/ci/make_latest_json.py <version> <setup_name> <setup_sha256> <portable_name> <portable_sha256>",
            file=sys.stderr,
        )
        return 2

    version, setup_name, setup_sha, portable_name, portable_sha = argv[1:]
    payload = {
        "version": version,
        "assets": [
            {"name": setup_name, "sha256": setup_sha},
            {"name": portable_name, "sha256": portable_sha},
        ],
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

