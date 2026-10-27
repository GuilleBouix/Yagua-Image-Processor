"""Fast source checks before downloading environments or compiling candidates."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ci.candidate_manifest import check_source_version  # noqa: E402
from scripts.ci.source_materials import safe_path, verify  # noqa: E402
from scripts.licensing import validate_catalog  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version')
    args = parser.parse_args()
    if args.version:
        check_source_version(args.version)
    validate_catalog(ROOT)
    manifest = json.loads((ROOT / 'legal/distribution/materials.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        if 'repository_path' in entry:
            verify(safe_path(ROOT, entry['repository_path']), entry)
    print('Source version, legal resources and local source-material hashes passed.')


if __name__ == '__main__':
    main()
