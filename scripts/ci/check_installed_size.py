"""Measure app + all models + execution caches, with compressed size separate."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ci.check_linux_size import MAX_BYTES, artifact_size, within_budget


def measure(app: Path, models: Path, caches: Path, compressed: Path) -> dict:
    paths = [path.resolve(strict=True) for path in (app, models, caches)]
    if any(a == b or a in b.parents or b in a.parents
           for index, a in enumerate(paths) for b in paths[index + 1:]):
        raise ValueError('App, models and caches must be separate, non-overlapping paths')
    components = dict(zip(('app', 'models', 'caches'), map(artifact_size, paths)))
    total = sum(components.values())
    return {
        'limit_bytes': MAX_BYTES, 'components_bytes': components,
        'installed_bytes': total, 'compressed_bytes': artifact_size(compressed),
        'within_budget': within_budget(total),
        'largest_files': [
            {'path': str(path.relative_to(root)), 'component': name, 'bytes': size}
            for size, name, root, path in sorted(
                ((path.stat().st_size, name, root, path)
                 for name, root in zip(components, paths)
                 for path in root.rglob('*') if path.is_file() and not path.is_symlink()),
                key=lambda item: item[0], reverse=True,
            )[:30]
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('app', 'models', 'caches', 'compressed', 'report'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    parser.add_argument('--measure-only', action='store_true', help='Baseline only; never a release gate')
    args = parser.parse_args(argv)
    report = measure(args.app, args.models, args.caches, args.compressed)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['within_budget'] or args.measure_only else 1


if __name__ == '__main__':
    raise SystemExit(main())
