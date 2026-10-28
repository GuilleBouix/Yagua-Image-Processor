"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. probe."""

import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from scripts.ci.stages.common import (
    PLATFORM, PYTHON, REPORTS, ROOT, VERSION, collect_reports, python, run, save, system, xvfb,
)


def main():
    """Ejecuta las pruebas aisladas del ejecutable o paquete generado."""
    system(packaging=True)
    REPORTS.mkdir(exist_ok=True)
    profile = Path(os.environ['RUNNER_TEMP']) / 'yagua-package-probe'
    try:
        if PLATFORM == 'windows':
            compressed = ROOT / f'installer/Yagua_Portable_{VERSION}.zip'
            app = ROOT / 'dist/Yagua'
            app.mkdir(parents=True)
            with zipfile.ZipFile(compressed) as archive:
                archive.extractall(app)
            run(PYTHON, 'scripts/ci/probe_package.py', app / 'Yagua.exe', profile)
            prefix, target = 'windows', 'win32'
        else:
            compressed = ROOT / f'dist/linux-release/Yagua-{VERSION}-x86_64.AppImage'
            compressed.chmod(0o755)
            directory = ROOT / 'build/linux-release/package-check'
            directory.mkdir(parents=True)
            subprocess.run([str(compressed), '--appimage-extract'], cwd=directory,
                           check=True, stdout=subprocess.DEVNULL)
            app = directory / 'squashfs-root'
            # El armado de AppImage puede reescribir los cargadores ELF de la copia AppDir.
            # Prueba el ejecutable PyInstaller original desde su checkpoint;
            # prueba después la copia empaquetada mediante AppRun y AppImage.
            xvfb(PYTHON, 'scripts/ci/probe_package.py', ROOT / 'dist/linux-release/Yagua/Yagua',
                 ROOT / 'reports/raw-preflight', '--preflight')
            xvfb(PYTHON, 'scripts/ci/probe_package.py', compressed,
                 ROOT / 'reports/appimage-runtime', '--preflight')
            xvfb(PYTHON, 'scripts/ci/probe_package.py', app / 'AppRun', profile)
            for source, name in [
                (REPORTS / 'raw-preflight/preflight/selftest.json', 'selftest-preflight.json'),
                (REPORTS / 'appimage-runtime/preflight/selftest.json', 'selftest-appimage-runtime.json'),
                (profile / 'online/selftest.json', 'selftest-online.json'),
                (profile / 'offline/selftest.json', 'selftest-offline.json'),
            ]:
                shutil.copy2(source, REPORTS / name)
            python('scripts/ci/build_heic_linux.py', '--check-package', app)
            prefix, target = 'linux', 'linux'
        size_report = 'windows-installed-size.json' if PLATFORM == 'windows' else 'installed-size.json'
        python('scripts/ci/check_installed_size.py', '--app', app, '--models', profile / 'models',
               '--caches', profile / 'caches', '--compressed', compressed, '--report', REPORTS / size_report)
        python('scripts/ci/check_licenses.py', '--package', app, '--platform', target,
               '--models', profile / 'models', '--report', REPORTS / f'{prefix}-licenses.json')
        if PLATFORM == 'linux':
            environment = os.environ.copy()
            environment['RELEASE_VERSION'] = VERSION
            python('scripts/ci/linux_validation_report.py', env=environment)
    finally:
        if profile.exists():
            collect_reports(profile, REPORTS / f'{PLATFORM}-probe')
    save('reports/*.json', 'reports/*.md', 'reports/*-probe/**/*.json', 'reports/*-probe/**/*.log',
         'reports/raw-preflight/**/*.json', 'reports/appimage-runtime/**/*.json')


if __name__ == '__main__':
    main()
