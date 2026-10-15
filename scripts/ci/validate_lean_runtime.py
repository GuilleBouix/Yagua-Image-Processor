"""Non-publishing, isolated baseline/candidate builds on the same machine.

Only the identical opt-in self-test instrumentation is overlaid on the baseline.
No versions, tags, releases, editor environments or personal profiles are changed.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def command(args, cwd, log, env=None):
    print('RUN', *map(str, args), flush=True)
    with log.open('a', encoding='utf-8') as output:
        subprocess.run(list(map(str, args)), cwd=cwd, env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True)


def validate(label: str, base_ref: str, reports: Path) -> dict:
    from scripts.ci.check_installed_size import measure
    from scripts.ci.audit_frozen import audit
    from scripts.ci.probe_package import isolated_environment
    destination = reports / label
    destination.mkdir()
    log = destination / 'build.log'
    with tempfile.TemporaryDirectory(prefix=f'yagua-{label}-') as temporary:
        task = Path(temporary)
        source = ROOT
        if label == 'baseline':
            archive = task / 'baseline.zip'
            command(['git', 'archive', '--format=zip', f'--output={archive}', base_ref], ROOT, log)
            source = task / 'source'
            with zipfile.ZipFile(archive) as zipped:
                zipped.extractall(source)
            # Same instrumentation/fixtures for both packages; original baseline
            # application logic, requirements and packaging policy stay unchanged.
            shutil.copy2(ROOT / 'app/utils/package_selftest.py', source / 'app/utils/package_selftest.py')
        build_env = task / 'build-env'
        command([sys.executable, '-m', 'venv', build_env], ROOT, log)
        python = build_env / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        requirements = 'requirements.txt' if os.name == 'nt' else 'requirements-linux-cpu.txt'
        args = [python, '-m', 'pip', 'install', '-r', requirements]
        if label != 'baseline':
            args += ['-r', 'requirements-build.txt']
        command(args, source, log)
        command([python, '-m', 'pip', 'check'], source, log)
        command([python, '-m', 'pip', 'freeze'], source, destination / 'dependencies.txt')
        dist, work = task / 'dist', task / 'work'
        env = isolated_environment(task / 'build-profile')
        env.pop('YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS', None)
        if label == 'baseline':
            env['YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS'] = '1'
        if os.name == 'nt':
            command([python, '-m', 'PyInstaller', '--clean', '--noconfirm',
                     '--distpath', dist, '--workpath', work, 'Yagua.spec'], source, log, env)
            package = dist / 'Yagua'
            executable = package / 'Yagua.exe'
            compressed = Path(shutil.make_archive(str(task / 'Yagua-portable'), 'zip', package))
        else:
            # AppImage tooling has its own environment; it cannot contaminate Analysis.
            tools = task / 'tools'
            command([sys.executable, '-m', 'venv', tools], ROOT, log)
            command([tools / 'bin/python', '-m', 'pip', 'install',
                     'setuptools==81.0.0', 'appimage-builder==1.1.0'], ROOT, log)
            env.update({
                'PATH': str(tools / 'bin') + os.pathsep + env['PATH'],
                'PYTHON_BIN': str(python), 'BUILD_DIR': str(work), 'DIST_DIR': str(dist),
                'TARGET_APPDIR': str(work / 'AppDir'), 'BUILD_APPIMAGE': '1',
                'PREFLIGHT_REPORT': str(destination / 'preflight.json'),
            })
            command(['bash', 'scripts/build_linux_appimage.sh'], source, log, env)
            compressed = next(dist.glob('*.AppImage'))
            package = work / 'package-check/squashfs-root'
            executable = package / 'AppRun'
            # Verify the actual AppImage runtime/restart path as well as extraction.
            command(['xvfb-run', '-a', sys.executable, ROOT / 'scripts/ci/probe_package.py',
                     compressed, task / 'runtime-probe', '--preflight'], ROOT, log, env)
            shutil.copy2(task / 'runtime-probe/preflight/selftest.json', destination / 'appimage-runtime.json')
        probe = task / 'probe'
        inventory = audit(package, work, enforce=label != 'baseline')
        (destination / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
        args = [sys.executable, ROOT / 'scripts/ci/probe_package.py', executable, probe]
        if os.name != 'nt':
            args = ['xvfb-run', '-a'] + args
        try:
            command(args, ROOT, log, env)
        finally:
            if probe.exists():
                for path in probe.glob('*/selftest.json'):
                    shutil.copy2(path, destination / f'{path.parent.name}.json')
                for path in probe.glob('*/process.log'):
                    shutil.copy2(path, destination / f'{path.parent.name}.log')
                if (probe / 'models-manifest.json').exists():
                    shutil.copy2(probe / 'models-manifest.json', destination / 'models.json')
        result = measure(package, probe / 'models', probe / 'caches', compressed)
        (destination / 'sizes.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        # Keep analysis evidence and warnings, not multi-gigabyte intermediate envs.
        for path in work.rglob('warn-*.txt'):
            shutil.copy2(path, destination / path.name)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='1914a11e9823bbf32af66631002e8db817c257e7')
    parser.add_argument('--reports', type=Path, required=True)
    args = parser.parse_args()
    reports = args.reports.resolve()
    reports.mkdir(parents=True, exist_ok=False)
    results = {'host': platform.platform(), 'processor': platform.processor(),
               'python': sys.version, 'baseline_ref': args.baseline}
    for label in ('baseline', 'candidate'):
        try:
            results[label] = validate(label, args.baseline, reports)
        except Exception:
            results[label] = {'error': traceback.format_exc(), 'within_budget': False}
            print(results[label]['error'], flush=True)
        (reports / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    if all('installed_bytes' in results[label] for label in ('baseline', 'candidate')):
        results['saved_bytes'] = results['baseline']['installed_bytes'] - results['candidate']['installed_bytes']
        probes = [json.loads((reports / label / 'offline.json').read_text(encoding='utf-8'))
                  for label in ('baseline', 'candidate')]
        results['image_contract_matches'] = probes[0]['image_roundtrips'] == probes[1]['image_roundtrips']
        results['background_contract_matches'] = probes[0]['background_roundtrips'] == probes[1]['background_roundtrips']
        results['numba_threading_matches'] = probes[0]['numba_threading_layer'] == probes[1]['numba_threading_layer']
    (reports / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))
    return 0 if (results['candidate']['within_budget'] and 'error' not in results['baseline']
                 and results.get('image_contract_matches')
                 and results.get('background_contract_matches')
                 and results.get('numba_threading_matches')) else 1


if __name__ == '__main__':
    raise SystemExit(main())
