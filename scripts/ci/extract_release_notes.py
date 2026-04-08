from __future__ import annotations

import re
import sys
from pathlib import Path


def _extract_section(md: str, header: str) -> str | None:
    # header is like: [Unreleased] or [2.0.0]
    # Accept: ## [X] or ## [X] - DATE
    pattern = re.compile(
        rf"^##\s+\[{re.escape(header)}\].*$\n(?P<body>.*?)(?=^##\s+\[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(md)
    if not m:
        return None
    return m.group("body").strip()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Uso: python scripts/ci/extract_release_notes.py <X.Y.Z[-pre]>", file=sys.stderr)
        return 2

    version = argv[1].strip()
    repo_root = Path(__file__).resolve().parents[2]
    changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")

    body = _extract_section(changelog, version)
    source = version
    if not body:
        body = _extract_section(changelog, "Unreleased") or ""
        source = "Unreleased"

    out = []
    out.append(f"## Yagua v{version}")
    out.append("")
    if body:
        out.append(body)
        out.append("")
    out.append(f"_Notas generadas desde CHANGELOG.md ({source})._")
    sys.stdout.write("\n".join(out).strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
