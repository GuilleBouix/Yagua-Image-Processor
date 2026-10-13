"""Combine successful frozen-package checks with measured artifact sizes."""

import json
import os
from pathlib import Path


def main() -> None:
    reports = Path('reports')
    preflight = json.loads((reports / 'selftest-preflight.json').read_text(encoding='utf-8'))
    online = json.loads((reports / 'selftest-online.json').read_text(encoding='utf-8'))
    offline = json.loads((reports / 'selftest-offline.json').read_text(encoding='utf-8'))
    sizes = json.loads(Path('dist/linux-release/sizes.json').read_text(encoding='utf-8'))
    assert preflight['status'] == 'passed' and preflight['mode'] == 'preflight'
    assert online['status'] == offline['status'] == 'passed'
    assert online['frozen'] and offline['frozen'] and offline['offline']
    assert all(item['bytes'] < 2_000_000_000 for item in sizes['artifacts'])
    (reports / 'sizes.json').write_text(json.dumps(sizes, indent=2) + '\n', encoding='utf-8')
    version = os.environ['RELEASE_VERSION']
    sha = os.environ['GITHUB_SHA']
    run_url = (f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/"
               f"{os.environ['GITHUB_RUN_ID']}")
    lines = [
        f'# Yagua Linux {version}', '',
        f'Commit: {sha}', f'Validation run: {run_url}', '',
        'Windows and Linux lint, types and tests passed before this build.',
        'The frozen PyInstaller directory passed native imports, CPU checks and packaged-resource preflight.',
        'The extracted AppImage passed startup, every registered module, real Spanish/English',
        'OCR, clipboard, TXT export and background removal with the default model.',
        'OCR and background removal passed again with network access blocked.',
        'CPU only; models download on first use and are not included in the distribution.', '',
        '## Measured sizes', '',
    ]
    lines.extend(f"- {Path(item['path']).name}: {item['bytes']:,} bytes"
                 for item in sizes['artifacts'])
    lines.extend(['', 'All distribution sizes are strictly below 2,000,000,000 bytes.',
                  '', 'Manual testing on an Ubuntu desktop is still pending.',
                  'For a prerelease, this is automated validation, not a stable-release approval.'])
    content = '\n'.join(lines) + '\n'
    (reports / 'validation.md').write_text(content, encoding='utf-8')
    if summary := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(summary, 'a', encoding='utf-8') as stream:
            stream.write(content)


if __name__ == '__main__':
    main()
