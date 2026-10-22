"""Verify repository or frozen-package legal resources without network access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.licensing import (  # noqa: E402
    installed_notices, package_resources, validate_catalog, verify_models, verify_package,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--package', type=Path)
    parser.add_argument('--platform', choices=['win32', 'linux'],
                        default='win32' if sys.platform == 'win32' else 'linux')
    parser.add_argument('--installed', action='store_true')
    parser.add_argument('--models', type=Path, help='Explicit temporary model directory; no downloads')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.package:
            report = verify_package(args.package, args.platform)
        else:
            catalog = validate_catalog(args.root)
            report = {'technical_status': 'passed', 'legal_approval': False,
                      'review_required': catalog['review_required']}
            if args.installed:
                _, report['installed'] = installed_notices(args.root, args.platform)
        if args.models:
            root = package_resources(args.package) if args.package else args.root
            report['models'] = verify_models(args.models, validate_catalog(root, check_requirements=not args.package))
    except (ValueError, OSError, KeyError, StopIteration) as error:
        print(f'Legal resource check failed: {error}', file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Legal resources: technical checks passed; legal review remains open (legal/REVIEW.md).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
