"""Small shared command, environment and checkpoint helpers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PYTHON = sys.executable
PLATFORM = os.environ.get('STAGE_PLATFORM', 'windows' if sys.platform == 'win32' else 'linux')
VERSION = os.environ.get('STAGE_VERSION', '')
REPORTS = ROOT / 'reports'


def run(*args, env=None, **kwargs):
    command = [str(arg) for arg in args]
    print('+ ' + ' '.join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=True, env=env, **kwargs)


def python(script, *args, **kwargs):
    return run(PYTHON, script, *args, **kwargs)


def pip(*args):
    run(PYTHON, '-m', 'pip', 'install', *args)


def system(packaging=False):
    if PLATFORM != 'linux':
        return
    packages = ['python3-tk', 'xvfb', 'xauth', 'fonts-dejavu-core', 'libgl1', 'libglib2.0-0',
                'libsm6', 'libxext6', 'libxrender1', 'libgtk-3-0', 'libgomp1']
    if packaging:
        packages += ['file', 'desktop-file-utils', 'libfuse2', 'patchelf', 'squashfs-tools',
                     'binutils', 'fakeroot', 'strace', 'zsync', 'libgdk-pixbuf2.0-dev',
                     'cmake', 'g++', 'make', 'nasm', 'patch', 'pkg-config']
    run('sudo', 'apt-get', 'update')
    run('sudo', 'apt-get', 'install', '-y', *packages)


def test_dependencies():
    system()
    pip('-r', 'requirements-linux-cpu.txt' if PLATFORM == 'linux' else 'requirements.txt',
        '-r', 'requirements-dev.txt')


def build_environment():
    environment = Path(os.environ.get('RUNNER_TEMP', str(ROOT / 'build'))) / 'yagua-build'
    run(PYTHON, '-m', 'venv', environment)
    interpreter = environment / ('Scripts/python.exe' if PLATFORM == 'windows' else 'bin/python')
    run(interpreter, '-m', 'pip', 'install', '-r',
        'requirements-linux-cpu.txt' if PLATFORM == 'linux' else 'requirements.txt',
        '-r', 'requirements-build.txt')
    run(interpreter, '-m', 'pip', 'check')
    return interpreter


def xvfb(*args, **kwargs):
    return run(*(['xvfb-run', '-a'] if PLATFORM == 'linux' else []), *args, **kwargs)


def paths(*patterns):
    result = set()
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            result.add(path.relative_to(ROOT).as_posix())
            if path.is_dir() and not path.is_symlink():
                result.update(p.relative_to(ROOT).as_posix() for p in path.rglob('*'))
    return sorted(result)


def save(*patterns):
    from scripts.ci.checkpoints import save as checkpoint
    return checkpoint(paths(*patterns))


def json_report(name, data):
    path = REPORTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def collect_reports(source, destination):
    source, destination = Path(source), Path(destination)
    for path in source.rglob('*'):
        if path.is_file() and path.suffix in {'.json', '.log'} and not any(
                part in {'models', 'caches'} for part in path.relative_to(source).parts):
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
