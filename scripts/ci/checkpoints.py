"""Verified, immutable checkpoints for resumable Actions jobs (standard library + PyYAML)."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import urllib.error
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.ci-state'
STAGES = {'quality', 'core', 'ui', 'compile', 'package', 'probe', 'installer', 'sources', 'deliver'}
VALIDATION = {'quality', 'core', 'ui'}


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def tracked() -> list[str]:
    return sorted(filter(None, git('ls-files', '-z').split('\0')))


def matches(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def stage_files(stage: str, platform: str, names: list[str]) -> list[str]:
    """Unknown inputs invalidate every stage; known inputs are assigned conservatively."""
    runtime = ('app/*', 'assets/*', 'legal/*', 'main.py', 'requirements.txt',
               'requirements-build.txt', 'scripts/licensing.py', 'scripts/packaging_rules.py',
               'scripts/pyinstaller/*', 'Yagua.spec' if platform == 'windows' else 'Yagua.linux.spec')
    if platform == 'linux':
        runtime += ('requirements-linux-cpu.txt', 'scripts/ci/build_heic_linux.py', 'scripts/build_linux_runtime.sh')
    common = ('scripts/ci/checkpoints.py', 'scripts/ci/stages/common.py',
              '.github/workflows/stage.yml', 'scripts/ci/stages/' + stage + '.py')
    policies = {
        'compile': runtime + (('scripts/build_linux_appimage.sh',) if platform == 'linux' else ()),
        'package': ('Yagua.iss', 'assets/installer/*', 'scripts/ci/make_latest_json.py')
        if platform == 'windows' else ('packaging/linux/*', 'assets/icon.png', 'scripts/build_linux_appimage.sh',
                                     'scripts/package_linux_appimage.sh', 'scripts/ci/check_linux_size.py'),
        'installer': ('scripts/ci/test_installer_finish.ps1',),
        'probe': ('scripts/ci/probe_package.py', 'scripts/ci/check_*', 'scripts/licensing.py',
                  'scripts/ci/build_heic_linux.py', 'scripts/ci/linux_validation_report.py'),
        'sources': ('scripts/ci/source_materials.py', 'legal/*'),
        'quality': ('app/*', 'scripts/*.py', 'scripts/*/*.py', 'scripts/*/*/*.py', 'tests/*',
                    'requirements*', '*.ini', '.github/workflows/*'),
        'core': ('app/*', 'assets/*', 'legal/*', 'scripts/*', 'tests/*', 'requirements*',
                 '*.spec', '*.iss', '*.ini', 'packaging/*', '.github/workflows/*', 'LICENSE', '*.md'),
        'ui': ('app/*', 'assets/*', 'legal/*', 'tests/ui/*', 'tests/conftest.py', 'tests/helpers*',
               'scripts/verify.py', 'requirements*', '*.ini'),
        'deliver': ('*',),
    }
    known = ('app/*', 'assets/*', 'legal/*', 'scripts/*', 'tests/*', 'docs/*', 'packaging/*',
             '.github/*', 'requirements*', '*.spec', '*.iss', '*.ini', '*.md', '*.txt',
             'main.py', 'LICENSE', '.gitignore', '.gitattributes', '.editorconfig')
    result = []
    for name in names:
        if stage == 'core' and name.startswith('tests/ui/'):
            continue
        if matches(name, common + policies[stage]) or not matches(name, known):
            result.append(name)
    return result


def fingerprint(stage: str, platform: str, version: str, dependencies: dict,
                environment: dict | None = None) -> tuple[str, dict]:
    files = {name: digest(ROOT / name) for name in stage_files(stage, platform, tracked())}
    # Hash the effective stage job, not sibling jobs in the same YAML document.
    workflow = ROOT / '.github/workflows' / ('validation.yml' if stage in VALIDATION else f'build-{platform}.yml')
    jobs = yaml.safe_load(workflow.read_text(encoding='utf-8'))['jobs']
    recipe = jobs.get(stage, {})
    consumed = {}
    for dependency, receipt in dependencies.items():
        entries = receipt['files']
        if stage == 'compile' or (stage == 'sources' and platform == 'windows'):
            entries = {}
        elif stage == 'probe':
            entries = {n: v for n, v in entries.items() if n.endswith(('.zip', '.AppImage', 'sizes.json'))}
        elif stage == 'installer':
            entries = {n: v for n, v in entries.items() if n.endswith('.exe')}
        elif stage == 'sources':
            entries = {n: v for n, v in entries.items() if n.endswith('linux-heic-native.json')}
        if entries:
            consumed[dependency] = entries
    environment = environment or {
        'os': platform, 'arch': os.environ.get('RUNNER_ARCH', ''),
        'image': os.environ.get('ImageOS', ''), 'image_version': os.environ.get('ImageVersion', ''),
        'python': sys.version.split()[0],
    }
    inputs = {'schema': 1, 'stage': stage, 'platform': platform, 'version': version,
              'files': files, 'recipe': recipe, 'environment': environment, 'dependencies': consumed}
    return encoded_hash(inputs), inputs


def api(path: str, *, raw: bool = False):
    token = os.environ.get('GH_TOKEN', '')
    url = path if path.startswith('https://') else f'https://api.github.com/repos/{os.environ["GITHUB_REPOSITORY"]}/{path}'
    request = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'yagua-checkpoints',
    })
    if raw:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        try:
            return urllib.request.build_opener(NoRedirect).open(request, timeout=120)
        except urllib.error.HTTPError as error:
            if error.code not in {301, 302, 303, 307, 308}:
                raise
            location = error.headers['Location']
            if not location.startswith('https://'):
                raise ValueError('Insecure artifact redirect') from error
            # Signed artifact storage receives no GitHub token.
            return urllib.request.urlopen(location, timeout=120)
    response = urllib.request.urlopen(request, timeout=120)
    with response:
        return json.load(response)


def pages(path: str, key: str) -> list:
    result = []
    for page in range(1, 11):
        separator = '&' if '?' in path else '?'
        data = api(f'{path}{separator}per_page=100&page={page}')[key]
        result.extend(data)
        if len(data) < 100:
            return result
    raise ValueError('Unexpected Actions pagination; refusing partial checkpoint discovery')


def safe_name(name: str) -> None:
    path = Path(name)
    if (not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
            or name.startswith('/')):
        raise ValueError(f'Unsafe checkpoint path: {name}')


def download(artifact: dict, target: Path) -> None:
    target.mkdir(parents=True)
    archive = target / 'download.zip'
    with api(artifact['archive_download_url'], raw=True) as response, archive.open('wb') as stream:
        shutil.copyfileobj(response, stream)
    expected = artifact.get('digest', '')
    if expected and expected != 'sha256:' + digest(archive):
        raise ValueError('Artifact SHA-256 mismatch')
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            safe_name(info.filename.rstrip('/'))
        zipped.extractall(target)
    archive.unlink()


def check_receipt(receipt: dict, directory: Path, platform: str) -> None:
    if (receipt.get('schema_version') != 1 or receipt.get('platform') != platform
            or receipt.get('stage') not in STAGES or receipt.get('status') != 'passed'):
        raise ValueError('Invalid checkpoint receipt/platform/status')
    payload = directory / 'payload.tar'
    if payload.stat().st_size != receipt['bytes'] or digest(payload) != receipt['sha256']:
        raise ValueError('Checkpoint payload SHA-256 mismatch')
    for name in receipt['files']:
        safe_name(name)


def receipt_for(artifact: dict) -> tuple[dict, dict]:
    """Read a small sidecar before deciding whether a large binary is needed."""
    run_id = artifact['workflow_run']['id']
    name = artifact['name'].replace('checkpoint-', 'receipt-', 1)
    sidecars = [item for item in pages(f'actions/runs/{run_id}/artifacts', 'artifacts')
                if item['name'] == name and not item['expired']]
    if len(sidecars) != 1:
        raise ValueError('Checkpoint receipt missing or expired')
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary) / 'receipt'
        download(sidecars[0], directory)
        receipt = json.loads((directory / 'receipt.json').read_text(encoding='utf-8'))
    if receipt.get('schema_version') != 1 or receipt.get('status') != 'passed':
        raise ValueError('Invalid checkpoint status/schema')
    expected = (f'checkpoint-{receipt["platform"]}-{receipt["stage"]}-{receipt["fingerprint"]}-'
                f'{receipt["producer"]["run_id"]}-{receipt["producer"]["attempt"]}')
    if artifact['name'] != expected:
        raise ValueError('Checkpoint receipt is not bound to its artifact')
    run = api(f'actions/runs/{run_id}')
    if not approved(receipt, run):
        raise ValueError('Checkpoint producer job did not pass')
    if not trusted(run) and str(run_id) != os.environ['GITHUB_RUN_ID']:
        raise ValueError('Untrusted checkpoint run')
    receipt['artifact_id'] = artifact['id']
    receipt['artifact_digest'] = artifact.get('digest')
    return receipt, run


def restore(receipt: dict, directory: Path, destination: Path) -> None:
    with tarfile.open(directory / 'payload.tar') as archive:
        for member in archive.getmembers():
            safe_name(member.name)
        archive.extractall(destination, filter='data')
    for name, entry in receipt['files'].items():
        path = destination / name
        if path.is_symlink():
            actual = {'link': os.readlink(path)}
        else:
            actual = {'bytes': path.stat().st_size, 'sha256': digest(path)}
        if actual != entry:
            raise ValueError(f'Checkpoint member mismatch: {name}')


def trusted(run: dict) -> bool:
    repository = os.environ['GITHUB_REPOSITORY']
    return (run.get('head_repository', {}).get('full_name') == repository
            and run.get('head_branch') == 'main' and run.get('event') in {'push', 'workflow_dispatch'}
            and run.get('path') in {'.github/workflows/ci.yml', '.github/workflows/candidates.yml',
                                    '.github/workflows/build-windows.yml', '.github/workflows/build-linux.yml'})


def approved(receipt: dict, run: dict) -> bool:
    producer = receipt['producer']
    if (str(producer['run_id']) != str(run['id']) or producer['commit'] != run['head_sha']
            or producer['repository'] != os.environ['GITHUB_REPOSITORY']):
        return False
    jobs = pages(f'actions/runs/{run["id"]}/attempts/{producer["attempt"]}/jobs', 'jobs')
    suffix = f'{receipt["platform"]} / {receipt["stage"]}'
    return any(job['name'].endswith(suffix) and job['conclusion'] == 'success' for job in jobs)


def candidate_runs(stage: str, resume: str, force: bool) -> list[dict]:
    if force or os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
        return []
    current = api(f'actions/runs/{os.environ["GITHUB_RUN_ID"]}')
    if not trusted(current):
        return []
    result = [current]
    if resume:
        previous = api(f'actions/runs/{int(resume)}')
        if not trusted(previous):
            raise ValueError('Resume run must originate from main in this repository')
        result.append(previous)
    if stage in VALIDATION:
        runs = api('actions/workflows/ci.yml/runs?branch=main&per_page=20')['workflow_runs']
        for run in runs:
            if str(run['id']) == os.environ['GITHUB_RUN_ID']:
                continue
            if run['head_sha'] == current['head_sha'] and run['status'] != 'completed':
                print(f'Waiting for existing CI: {run["html_url"]}', flush=True)
                while run['status'] != 'completed':
                    time.sleep(30)
                    run = api(f'actions/runs/{run["id"]}')
            if run['status'] == 'completed' and trusted(run):
                result.append(run)
    return list({run['id']: run for run in result}.values())


def output(name: str, value: str) -> None:
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write(f'{name}={value}\n')


def summary(message: str) -> None:
    print(message, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(message + '\n')


def prepare(stage: str, platform: str, version: str, dependencies: dict,
            resume: str, force: bool) -> None:
    STATE.mkdir(exist_ok=True)
    receipts = {}
    lineage = {}
    payloads = {}
    for name, artifact_id in dependencies.items():
        artifact = api(f'actions/artifacts/{int(artifact_id)}')
        receipt, _ = receipt_for(artifact)
        if receipt['stage'] != name or receipt['platform'] != platform:
            raise ValueError('Dependency stage/platform mismatch')
        receipts[name] = receipt
        payloads[name] = artifact
        lineage.update(receipt.get('lineage', {}))
        lineage[name] = {k: v for k, v in receipt.items() if k != 'lineage'}
    # Direct receipts override ancestry imported from older successful builds.
    lineage.update({name: {k: v for k, v in receipt.items() if k != 'lineage'}
                    for name, receipt in receipts.items()})
    key, inputs = fingerprint(stage, platform, version, receipts)
    context = {'stage': stage, 'platform': platform, 'version': version, 'fingerprint': key,
               'started_at': time.time(),
               'inputs': inputs, 'lineage': lineage}
    (STATE / 'context.json').write_text(json.dumps(context, indent=2), encoding='utf-8')
    output('reused', 'false')
    output('fingerprint', key)
    if stage != 'deliver':
        for run in candidate_runs(stage, resume, force):
            artifacts = pages(f'actions/runs/{run["id"]}/artifacts', 'artifacts')
            prefix = f'checkpoint-{platform}-{stage}-{key}-'
            for artifact in sorted(artifacts, key=lambda item: item['id'], reverse=True):
                if not artifact['name'].startswith(prefix) or artifact['expired']:
                    continue
                try:
                    receipt, _ = receipt_for(artifact)
                    if receipt['fingerprint'] != key or receipt['platform'] != platform:
                        continue
                    receipt['lineage'] = lineage
                    (STATE / 'reused.json').write_text(json.dumps(receipt), encoding='utf-8')
                    output('reused', 'true')
                    output('artifact_id', str(artifact['id']))
                    summary(f'### {platform} / {stage}: reused\nOrigin: {receipt["producer"]}\n')
                    return
                except (ValueError, KeyError, OSError, tarfile.TarError, zipfile.BadZipFile) as error:
                    summary(f'Ignored unusable checkpoint {artifact["id"]}: {error}')
            if (stage in VALIDATION and run.get('path') == '.github/workflows/ci.yml'
                    and run.get('head_sha') == os.environ.get('GITHUB_SHA')
                    and run.get('status') == 'completed' and run.get('conclusion') != 'success'):
                jobs = pages(f'actions/runs/{run["id"]}/jobs', 'jobs')
                if any(job['name'].endswith(f'{platform} / {stage}')
                       and job['conclusion'] in {'failure', 'timed_out', 'cancelled'} for job in jobs):
                    raise RuntimeError(f'Existing CI failed this validation; fix or retry run {run["id"]} first')
    for name, artifact in payloads.items():
        if stage == 'compile':
            continue  # Validation receipts are gates, not runtime compilation inputs.
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'checkpoint'
            download(artifact, directory)
            check_receipt(receipts[name], directory, platform)
            restore(receipts[name], directory, ROOT)
    summary(f'### {platform} / {stage}: execute\nInput fingerprint: `{key}`\n')


def save(paths: list[str]) -> dict:
    context = json.loads((STATE / 'context.json').read_text())
    directory = STATE / 'upload'
    directory.mkdir()
    files = {}
    with tarfile.open(directory / 'payload.tar', 'w') as archive:
        for name in sorted(set(paths)):
            safe_name(name)
            path = ROOT / name
            archive.add(path, arcname=name, recursive=False)
            if path.is_file() or path.is_symlink():
                files[name] = ({'link': os.readlink(path)} if path.is_symlink() else
                               {'bytes': path.stat().st_size, 'sha256': digest(path)})
    producer = {'repository': os.environ.get('GITHUB_REPOSITORY', 'local'),
                'commit': git('rev-parse', 'HEAD'), 'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
                'attempt': os.environ.get('GITHUB_RUN_ATTEMPT', '1'), 'python': sys.version,
                'image': os.environ.get('ImageVersion', '')}
    receipt = {**context, 'schema_version': 1, 'status': 'passed', 'producer': producer,
               'elapsed_seconds': round(time.time() - context.get('started_at', time.time()), 2),
               'files': files, 'bytes': (directory / 'payload.tar').stat().st_size,
               'sha256': digest(directory / 'payload.tar')}
    (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    summary(f'Checkpoint saved: {receipt["bytes"]:,} uncompressed bytes; '
            f'{receipt["elapsed_seconds"]:.2f} seconds. Producer: {producer}')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=sorted(STAGES), required=True)
    parser.add_argument('--platform', choices=['windows', 'linux'], required=True)
    parser.add_argument('--version', default='')
    parser.add_argument('--dependencies', default='{}')
    parser.add_argument('--resume-run-id', default='')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if not args.version:
        import ast
        tree = ast.parse((ROOT / 'app/version.py').read_text())
        args.version = next(ast.literal_eval(node.value) for node in tree.body
                            if isinstance(node, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets))
    prepare(args.stage, args.platform, args.version, json.loads(args.dependencies),
            args.resume_run_id, args.force or os.environ.get('STAGE_FORCE') == 'true')


if __name__ == '__main__':
    main()
