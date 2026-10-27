import os
from pathlib import Path

from scripts.ci.stages.common import PLATFORM, REPORTS, ROOT, VERSION, python, save


def main():
    REPORTS.mkdir(exist_ok=True)
    args = ['--cache', str(Path(os.environ['RUNNER_TEMP']) / 'yagua-source-materials'),
            '--output', f'reports/Yagua-{VERSION}-source-materials.tar.xz', '--download',
            '--candidate-commit', os.environ['GITHUB_SHA']]
    if PLATFORM == 'linux':
        args += ['--native-build-report', str(ROOT / 'dist/linux-release/linux-heic-native.json')]
    python('scripts/ci/source_materials.py', *args)
    save('reports/Yagua-*-source-materials.tar.xz', 'dist/linux-release/linux-heic-native.json')


if __name__ == '__main__':
    main()
