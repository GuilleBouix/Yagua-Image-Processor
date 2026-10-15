"""Run a frozen app with a disposable profile and shared online/offline models."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def run(executable: Path, root: Path, label: str, mode='full') -> dict:
    home = root / label
    home.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    paths = {
        'APPDATA': root / 'caches/profile',
        'XDG_CONFIG_HOME': root / 'caches/config',
        'XDG_CACHE_HOME': root / 'caches/xdg',
        'TORCH_HOME': root / 'caches/torch',
        'NUMBA_CACHE_DIR': root / 'caches/numba',
        'EASYOCR_MODULE_PATH': root / 'models/easyocr',
        'U2NET_HOME': root / 'models/rembg',
    }
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path.resolve())
    env.update({
        'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
        'YAGUA_PACKAGE_SELFTEST': str((home / 'selftest.json').resolve()),
        'YAGUA_PACKAGE_SELFTEST_MODE': mode,
        'YAGUA_PACKAGE_OFFLINE': '1' if label == 'offline' else '0',
    })
    started = time.perf_counter()
    with (home / 'process.log').open('w', encoding='utf-8') as log:
        completed = subprocess.run([str(executable.resolve())], cwd=home, env=env,
                                   stdout=log, stderr=subprocess.STDOUT, timeout=1200)
    report = json.loads((home / 'selftest.json').read_text(encoding='utf-8'))
    report['process_seconds'] = time.perf_counter() - started
    report['exit_code'] = completed.returncode
    (home / 'selftest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if completed.returncode or report['status'] != 'passed':
        raise RuntimeError(f'Package verification failed: {home / "selftest.json"}\n{report}')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('root', type=Path)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    if args.root.exists():
        parser.error('Use a new root to prove downloads and cache reuse')
    args.root.mkdir(parents=True)
    if args.preflight:
        run(args.executable, args.root, 'preflight', 'preflight')
        return
    for repetition in range(3):
        run(args.executable, args.root, f'startup-{repetition + 1}', 'startup')
    run(args.executable, args.root, 'online')
    before = {str(path.relative_to(args.root / 'models')): path.stat().st_size
              for path in (args.root / 'models').rglob('*') if path.is_file()}
    if len([path for path in before if path.endswith(('.pth', '.onnx'))]) != 5:
        raise RuntimeError(f'Expected CRAFT, English, Latin, ISNet and U2NetP: {before}')
    run(args.executable, args.root, 'offline')
    after = {str(path.relative_to(args.root / 'models')): path.stat().st_size
             for path in (args.root / 'models').rglob('*') if path.is_file()}
    if before != after:
        raise RuntimeError('Model cache changed during offline reuse')


if __name__ == '__main__':
    main()
