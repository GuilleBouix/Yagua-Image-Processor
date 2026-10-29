"""Verified, immutable checkpoints for resumable Actions jobs (standard library + PyYAML)."""
# Verifica y transfiere checkpoints inmutables para reanudar jobs de CI.
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import fnmatch
import hashlib
import http.client
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
CLASSIFIED_SCRIPTS = (
    'scripts/build_linux_appimage.sh', 'scripts/build_linux_runtime.sh',
    'scripts/package_linux_appimage.sh', 'scripts/build_macos_app.sh', 'scripts/build_windows.ps1',
    'scripts/check_mutations.py', 'scripts/licensing.py', 'scripts/packaging_rules.py', 'scripts/verify.py',
    'scripts/pyinstaller/*', 'scripts/ci/apply_version.py', 'scripts/ci/audit_frozen.py',
    'scripts/ci/build_heic_linux.py', 'scripts/ci/candidate_manifest.py', 'scripts/ci/check_installed_size.py',
    'scripts/ci/check_licenses.py', 'scripts/ci/check_linux_size.py', 'scripts/ci/checkpoint_fixture.py',
    'scripts/ci/checkpoints.py', 'scripts/ci/extract_release_notes.py', 'scripts/ci/final_exports.py',
    'scripts/ci/linux_validation_report.py', 'scripts/ci/make_latest_json.py', 'scripts/ci/partitions.py',
    'scripts/ci/preflight.py', 'scripts/ci/probe_package.py', 'scripts/ci/source_materials.py',
    'scripts/ci/test_installer_finish.ps1', 'scripts/ci/validate_lean_runtime.py',
    'scripts/ci/stages/__init__.py', 'scripts/ci/stages/common.py',
) + tuple(f'scripts/ci/stages/{stage}.py' for stage in STAGES)
CLASSIFIED_WORKFLOWS = tuple('.github/workflows/' + name for name in (
    'build-linux.yml', 'build-windows.yml', 'candidates.yml', 'ci.yml', 'lean-runtime.yml',
    'release-linux.yml', 'release.yml', 'stage.yml', 'validation.yml', 'checkpoint-selftest.yml'))


def digest(path: Path) -> str:
    """Calcula el SHA-256 de un archivo antes de reutilizarlo."""
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded_hash(value) -> str:
    """Normaliza una huella codificada para compararla con el recibo."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def git(*args: str) -> str:
    """Consulta datos del repositorio necesarios para crear huellas reproducibles."""
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def tracked() -> list[str]:
    """Obtiene la lista de archivos versionados que influyen en el candidato."""
    return sorted(filter(None, git('ls-files', '-z').split('\0')))


def matches(name: str, patterns: tuple[str, ...]) -> bool:
    """Comprueba si una ruta coincide con alguno de los patrones de una etapa."""
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def stage_files(stage: str, platform: str, names: list[str]) -> list[str]:
    """Unknown inputs invalidate every stage; known inputs are assigned conservatively."""
    runtime = ('app/*', 'assets/*', 'legal/*', 'main.py', 'requirements.txt',
               'requirements-build.txt', 'scripts/licensing.py', 'scripts/packaging_rules.py',
               'scripts/pyinstaller/*', 'Yagua.spec' if platform == 'windows' else 'Yagua.linux.spec')
    if platform == 'linux':
        runtime += ('requirements-linux-cpu.txt', 'scripts/ci/build_heic_linux.py', 'scripts/build_linux_runtime.sh')
    # Las pruebas de core/quality no cambian el
    # programa compilado ni los tests de interfaz. La selección de entradas,
    # la receta efectiva y el entorno siguen definiendo la huella.
    common = ('scripts/ci/stages/common.py',
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
        'ui': ('app/*', 'assets/*', 'legal/*', 'tests/*',
               'scripts/verify.py', 'scripts/ci/partitions.py', 'requirements*', '*.ini'),
        'deliver': ('*',),
    }
    known = ('app/*', 'assets/*', 'legal/*', 'tests/*', 'docs/*', 'packaging/linux/*',
             '.github/ISSUE_TEMPLATE/*', '.github/FUNDING.yml', 'requirements*', '*.spec', '*.iss',
             '*.ini', '*.md', '*.txt', 'main.py', 'LICENSE', '.gitignore', '.gitattributes',
             '.editorconfig') + CLASSIFIED_SCRIPTS + CLASSIFIED_WORKFLOWS
    result = []
    for name in names:
        if stage == 'core' and name.startswith('tests/ui/'):
            continue
        if stage == 'core' and name == 'scripts/ci/test_installer_finish.ps1':
            continue  # Exercised by the real installer job, not by the Python service tests.
        if (stage == 'ui' and name.startswith('tests/') and not name.startswith('tests/ui/')
                and Path(name).name.startswith('test_') and name.endswith('.py')):
            continue  # Non-UI test modules are not shared helpers or image fixtures.
        if matches(name, common + policies[stage]) or not matches(name, known):
            result.append(name)
    return result


def fingerprint(stage: str, platform: str, version: str, dependencies: dict,
                environment: dict | None = None) -> tuple[str, dict]:
    """Calcula la huella de entradas, receta y entorno para una etapa."""
    files = {name: digest(ROOT / name) for name in stage_files(stage, platform, tracked())}
    # Calcula el hash del job de esta etapa, no de los jobs hermanos del mismo YAML.
    workflow = ROOT / '.github/workflows' / ('validation.yml' if stage in VALIDATION else f'build-{platform}.yml')
    jobs = yaml.safe_load(workflow.read_text(encoding='utf-8'))['jobs']
    recipe = jobs.get(stage, {})
    consumed = {}
    for dependency, receipt in dependencies.items():
        entries = receipt['files']
        if stage == 'compile' or (stage == 'sources' and platform == 'windows'):
            entries = {}
        elif stage == 'probe':
            if dependency != 'compile':
                entries = {n: v for n, v in entries.items() if n.endswith(('.zip', '.AppImage', 'sizes.json'))}
        elif stage == 'installer':
            entries = {n: v for n, v in entries.items() if n.endswith('.exe')}
        elif stage == 'sources':
            entries = {n: v for n, v in entries.items() if n.endswith('linux-heic-native.json')}
        if entries:
            consumed[dependency] = entries
    environment = environment or {
        'os': platform, 'arch': os.environ.get('RUNNER_ARCH', ''),
        'image': os.environ.get('ImageOS', ''),
        'python': sys.version.split()[0],
    }
    inputs = {'schema': 1, 'stage': stage, 'platform': platform, 'version': version,
              'files': files, 'recipe': recipe, 'environment': environment, 'dependencies': consumed}
    return encoded_hash(inputs), inputs


def retry_network(operation):
    """Reintenta solo fallos de transporte y no los trata como caché vacía."""
    for attempt in range(3):
        try:
            return operation()
        except urllib.error.HTTPError as error:
            if error.code in {404, 410}:
                raise
            if error.code != 429 and error.code < 500:
                raise RuntimeError(f'Actions request refused ({error.code}); checkpoints retained') from error
            retry_after = error.headers.get('Retry-After', '') if error.headers else ''
            delay = min(60, float(retry_after)) if retry_after.isdigit() else 10 * (attempt + 1)
            cause = error
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as error:
            delay, cause = 10 * (attempt + 1), error
        if attempt < 2:
            print(f'Temporary Actions transport failure; retrying in {delay}s: {cause}', flush=True)
            time.sleep(delay)
        else:
            raise RuntimeError('Actions transport unavailable; retry this job without rebuilding prior stages') from cause


def api(path: str, *, raw: bool = False):
    """Consulta GitHub con límites y credenciales adecuados al tipo de recurso."""
    token = os.environ.get('GH_TOKEN', '')
    url = path if path.startswith('https://') else f'https://api.github.com/repos/{os.environ["GITHUB_REPOSITORY"]}/{path}'
    request = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'yagua-checkpoints',
    })
    if raw:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            """Impide seguir redirecciones al transferir artefactos con URL firmada."""
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                """Rechaza redirecciones para no reenviar datos de acceso a otro host."""
                return None
        def open_download():
            """Abre una URL de artefacto con firma sin enviar el token de GitHub."""
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
        return retry_network(open_download)
    def read_json():
        """Lee y decodifica una respuesta JSON de GitHub."""
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    return retry_network(read_json)


def pages(path: str, key: str) -> list:
    """Recorre las páginas de una colección devuelta por la API."""
    result = []
    for page in range(1, 11):
        separator = '&' if '?' in path else '?'
        data = api(f'{path}{separator}per_page=100&page={page}')[key]
        result.extend(data)
        if len(data) < 100:
            return result
    raise ValueError('Unexpected Actions pagination; refusing partial checkpoint discovery')


def safe_name(name: str) -> None:
    """Rechaza nombres de artefacto que puedan escapar del directorio esperado."""
    path = Path(name)
    if (not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
            or name.startswith('/')):
        raise ValueError(f'Unsafe checkpoint path: {name}')


def download(artifact: dict, target: Path) -> None:
    """Descarga y valida un artefacto en una ruta temporal segura."""
    target.mkdir(parents=True)
    archive = target / 'download.zip'
    def transfer():
        """Copia la respuesta del servidor y verifica su tamaño y hash."""
        with api(artifact['archive_download_url'], raw=True) as response, archive.open('wb') as stream:
            shutil.copyfileobj(response, stream)
    retry_network(transfer)
    expected = artifact.get('digest', '')
    if expected and expected != 'sha256:' + digest(archive):
        raise ValueError('Artifact SHA-256 mismatch')
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            safe_name(info.filename.rstrip('/'))
        zipped.extractall(target)
    archive.unlink()


def check_receipt(receipt: dict, directory: Path, platform: str) -> None:
    """Valida el recibo y los bytes de un checkpoint antes de restaurarlo."""
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
    """Restaura un checkpoint validado en el destino de trabajo."""
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
    """Determina si una ejecución origen pertenece a un flujo confiable."""
    repository = os.environ['GITHUB_REPOSITORY']
    return (run.get('head_repository', {}).get('full_name') == repository
            and run.get('head_branch') == 'main' and run.get('event') in {'push', 'workflow_dispatch'}
            and run.get('path') in {'.github/workflows/ci.yml', '.github/workflows/candidates.yml',
                                    '.github/workflows/build-windows.yml', '.github/workflows/build-linux.yml'})


def approved(receipt: dict, run: dict) -> bool:
    """Comprueba que el recibo esté aprobado para reutilizarse en esta etapa."""
    producer = receipt['producer']
    if (str(producer['run_id']) != str(run['id']) or producer['commit'] != run['head_sha']
            or producer['repository'] != os.environ['GITHUB_REPOSITORY']):
        return False
    jobs = pages(f'actions/runs/{run["id"]}/attempts/{producer["attempt"]}/jobs', 'jobs')
    suffix = f'{receipt["platform"]} / {receipt["stage"]}'
    return any(job['name'].endswith(suffix) and job['conclusion'] == 'success' for job in jobs)


def candidate_runs(stage: str, resume: str, force: bool, platform: str = '') -> list[dict]:
    """Busca ejecuciones previas compatibles con la etapa y la versión solicitadas."""
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
        # Una recuperación anterior puede haber reutilizado un productor antiguo sin
        # volver a subir su carga grande. Sigue también candidatos recientes y confiables
        # para que un nuevo arreglo pueda recuperar ese checkpoint original.
        latest = api('actions/runs?branch=main&event=workflow_dispatch&per_page=100')['workflow_runs']
        selected_time = datetime.fromisoformat(previous['created_at'].replace('Z', '+00:00'))
        cutoff = selected_time - timedelta(days=7)
        for ancestor in latest:
            created = datetime.fromisoformat(ancestor['created_at'].replace('Z', '+00:00'))
            if (cutoff <= created <= selected_time and trusted(ancestor)
                    and ancestor.get('path') != '.github/workflows/ci.yml'):
                result.append(ancestor)
    if stage in VALIDATION:
        runs = api('actions/workflows/ci.yml/runs?branch=main&per_page=20')['workflow_runs']
        for run in runs:
            if str(run['id']) == os.environ['GITHUB_RUN_ID']:
                continue
            if run['head_sha'] == current['head_sha'] and run['status'] != 'completed':
                print(f'Waiting for existing CI stage {platform}/{stage}: {run["html_url"]}', flush=True)
                while run['status'] != 'completed':
                    jobs = pages(f'actions/runs/{run["id"]}/jobs', 'jobs')
                    selected = [job for job in jobs if job['name'].endswith(f'{platform} / {stage}')]
                    if selected and all(job['status'] == 'completed' for job in selected):
                        break
                    time.sleep(30)
                    run = api(f'actions/runs/{run["id"]}')
            if (run['status'] == 'completed' or run['head_sha'] == current['head_sha']) and trusted(run):
                result.append(run)
    return list({run['id']: run for run in result}.values())


def output(name: str, value: str) -> None:
    """Escribe un valor en el archivo de salida de GitHub Actions."""
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write(f'{name}={value}\n')


def summary(message: str) -> None:
    """Agrega un bloque legible al resumen del job."""
    print(message, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(message + '\n')


def prepare(stage: str, platform: str, version: str, dependencies: dict,
            resume: str, force: bool) -> None:
    """Decide si reutilizar un checkpoint o ejecutar la etapa desde cero."""
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
    # Los recibos directos tienen prioridad sobre la procedencia importada de builds anteriores.
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
        for run in candidate_runs(stage, resume, force, platform):
            artifacts = pages(f'actions/runs/{run["id"]}/artifacts', 'artifacts')
            prefix = f'checkpoint-{platform}-{stage}-{key}-'
            for artifact in sorted(artifacts, key=lambda item: item['id'], reverse=True):
                if not artifact['name'].startswith(prefix) or artifact['expired']:
                    continue
                try:
                    receipt, _ = receipt_for(artifact)
                    if receipt['fingerprint'] != key or receipt['platform'] != platform:
                        continue
                    # Valida los bytes del productor reutilizable antes de aprobar este job.
                    # Si el checkpoint está dañado, ejecuta esta etapa en su propio job
                    # en lugar de hacer fallar repetidamente a los jobs posteriores.
                    with tempfile.TemporaryDirectory() as temporary:
                        directory = Path(temporary) / 'checkpoint'
                        download(artifact, directory)
                        check_receipt(receipt, directory, platform)
                    receipt['lineage'] = lineage
                    (STATE / 'reused.json').write_text(json.dumps(receipt), encoding='utf-8')
                    output('reused', 'true')
                    output('artifact_id', str(artifact['id']))
                    summary(f'### {platform} / {stage}: reused\nOrigin: {receipt["producer"]}\n')
                    return
                except urllib.error.HTTPError as error:
                    if error.code not in {404, 410}:
                        raise
                    summary(f'Checkpoint {artifact["id"]} is no longer available: {error}')
                except (ValueError, KeyError, FileNotFoundError, tarfile.TarError, zipfile.BadZipFile) as error:
                    summary(f'Ignored unusable checkpoint {artifact["id"]}: {error}')
            if (stage in VALIDATION and run.get('path') == '.github/workflows/ci.yml'
                    and run.get('head_sha') == os.environ.get('GITHUB_SHA')
                    and run.get('conclusion') != 'success'):
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
    """Publica los artefactos de esta etapa junto con su recibo de integridad."""
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
    """Prepara o guarda checkpoints verificables para reanudar jobs de Actions."""
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
