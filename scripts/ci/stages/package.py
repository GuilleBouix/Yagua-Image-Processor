"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. package."""

import json
import os
from pathlib import Path
import zipfile

from scripts.ci.checkpoints import digest
from scripts.ci.stages.common import PLATFORM, PYTHON, ROOT, VERSION, pip, run, save, system


def main():
    """Empaqueta la aplicación y comprueba los recursos incluidos."""
    if PLATFORM == 'windows':
        run('choco', 'install', 'innosetup', '-y')
        # La carpeta de instalación de Chocolatey puede no estar en PATH en este proceso.
        compiler = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Inno Setup 6/ISCC.exe'
        run(compiler if compiler.exists() else 'iscc', 'Yagua.iss')
        setup = ROOT / f'installer/Yagua_Setup_{VERSION}.exe'
        portable = ROOT / f'installer/Yagua_Portable_{VERSION}.zip'
        with zipfile.ZipFile(portable, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((ROOT / 'dist/Yagua').rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(ROOT / 'dist/Yagua'))
        for path in (setup, portable):
            path.with_name(path.name + '.sha256').write_text(f'{digest(path)}  {path.name}\n', encoding='ascii')
        latest = run(PYTHON, 'scripts/ci/make_latest_json.py', VERSION,
                     setup.name, digest(setup), portable.name, digest(portable), capture_output=True, text=True)
        (ROOT / 'installer/latest.json').write_text(latest.stdout, encoding='utf-8')
        save('installer/Yagua_*.exe', 'installer/Yagua_*.zip', 'installer/*.sha256', 'installer/latest.json')
    else:
        system(packaging=True)
        tools = Path(os.environ['RUNNER_TEMP']) / 'yagua-appimage-tools'
        run(PYTHON, '-m', 'venv', tools)
        run(tools / 'bin/python', '-m', 'pip', 'install', 'setuptools==81.0.0', 'appimage-builder==1.1.0')
        pip('packaging==26.0')
        environment = os.environ.copy()
        environment.update(PYTHON_BIN=PYTHON, BUILD_PHASE='appimage', BUILD_APPIMAGE='1',
                           BUILD_DIR=str(ROOT / 'build/linux-release'),
                           DIST_DIR=str(ROOT / 'dist/linux-release'),
                           TARGET_APPDIR=str(ROOT / 'build/linux-release/AppDir'), APP_VERSION=VERSION,
                           PATH=str(tools / 'bin') + os.pathsep + os.environ['PATH'])
        run('bash', 'scripts/build_linux_appimage.sh', env=environment)
        save('dist/linux-release/*.AppImage', 'dist/linux-release/*.sha256', 'dist/linux-release/sizes.json',
             'dist/linux-release/linux-heic-native.json')
    # Mantén separado el commit fuente del productor del runtime registrado en la cadena del recibo.
    print(json.dumps({'status': 'packaged', 'version': VERSION}))


if __name__ == '__main__':
    main()
