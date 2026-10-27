import os
from pathlib import Path
import shutil

from scripts.ci.stages.common import ROOT, VERSION, run, save


def main():
    directory = Path(os.environ['RUNNER_TEMP']) / 'yagua-installer-finish'
    try:
        run('pwsh', '-NoProfile', '-File', 'scripts/ci/test_installer_finish.ps1',
            '-Installer', ROOT / f'installer/Yagua_Setup_{VERSION}.exe', '-WorkDirectory', directory)
    finally:
        if directory.exists():
            shutil.copytree(directory, ROOT / 'reports/installer-finish',
                            ignore=shutil.ignore_patterns('install-*'), dirs_exist_ok=True)
    save('reports/installer-finish/**/*.log', 'reports/installer-finish/**/*.json',
         'reports/installer-finish/**/*.png')


if __name__ == '__main__':
    main()
