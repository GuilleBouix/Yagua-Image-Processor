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


def comparison_checks(results: dict) -> list[dict]:
    from scripts.ci.check_linux_size import MAX_BYTES

    checks = []
    for label in ('baseline', 'candidate'):
        error = results[label].get('error')
        checks.append({'name': f'{label}-package', 'status': 'failed' if error else 'passed',
                       'detail': f'See {label}/build.log' if error else 'Build, imports, UI, models online/offline passed'})
    candidate = results['candidate']
    total = candidate.get('installed_bytes')
    if total is None:
        checks.append({'name': 'installed-size', 'status': 'skipped', 'detail': 'No complete candidate measurement'})
    else:
        limit = candidate.get('limit_bytes', MAX_BYTES)
        passed = candidate['within_budget']
        detail = f'App + models + caches: {total:,} bytes; required: < {limit:,} bytes'
        if not passed:
            detail += f'; reduce by at least {max(1, total - limit + 1):,} bytes'
        checks.append({'name': 'installed-size', 'status': 'passed' if passed else 'failed', 'detail': detail})
    for key, name, detail in (
        ('image_contract_matches', 'image-pixels', 'Nine formats: same decoded pixels, mode and dimensions'),
        ('background_contract_matches', 'background-pixels', 'ISNet and U2NetP: same decoded pixels'),
        ('numba_threading_matches', 'numba-backend', 'Same Numba threading backend as baseline'),
    ):
        value = results.get(key)
        checks.append({'name': name, 'status': 'skipped' if value is None else 'passed' if value else 'failed',
                       'detail': detail if value is not None else 'Requires both package checks to complete'})
    return checks


def write_summary(results: dict, reports: Path) -> bool:
    results['checks'] = comparison_checks(results)
    results['failed_checks'] = [check['name'] for check in results['checks'] if check['status'] == 'failed']
    lines = ['# Lean runtime validation', '', '| Check | Result | Detail |', '|---|---|---|']
    for check in results['checks']:
        lines.append(f"| {check['name']} | {check['status']} | {check['detail']} |")
        stream = sys.stderr if check['status'] == 'failed' else sys.stdout
        print(f"{check['status'].upper()}: {check['name']}: {check['detail']}", file=stream, flush=True)
    if 'saved_bytes' in results:
        lines += ['', f"Saved bytes: {results['saved_bytes']:,}. Positive means smaller than baseline.",
                  'The size gate uses the absolute installed total, not the amount saved.']
    content = '\n'.join(lines) + '\n'
    (reports / 'summary.md').write_text(content, encoding='utf-8')
    if path := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(path, 'a', encoding='utf-8') as output:
            output.write(content)
    return all(check['status'] == 'passed' for check in results['checks'])


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
    passed = write_summary(results, reports)
    (reports / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
