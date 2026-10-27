import os

from scripts.ci.stages.common import PLATFORM, ROOT, build_environment, run, save, system


def main():
    system(packaging=True)
    interpreter = build_environment()
    if PLATFORM == 'windows':
        run(interpreter, '-m', 'PyInstaller', '--clean', '--noconfirm', 'Yagua.spec')
        save('dist/Yagua')
    else:
        environment = os.environ.copy()
        environment.update(PYTHON_BIN=str(interpreter), BUILD_PHASE='runtime',
                           BUILD_DIR=str(ROOT / 'build/linux-release'),
                           DIST_DIR=str(ROOT / 'dist/linux-release'), BUILD_APPIMAGE='0')
        run('bash', 'scripts/build_linux_appimage.sh', env=environment)
        save('dist/linux-release/Yagua', 'dist/linux-release/linux-heic-native.json',
             'dist/linux-release/licenses.json')


if __name__ == '__main__':
    main()
