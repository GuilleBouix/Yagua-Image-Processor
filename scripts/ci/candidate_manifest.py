"""Record candidate inputs and verify the exact files before publication."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def check_source_version(expected: str) -> None:
    module = ast.parse((ROOT / 'app/version.py').read_text(encoding='utf-8'))
    values = [ast.literal_eval(node.value) for node in module.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == '__version__'
                      for target in node.targets)]
    if values != [expected]:
        raise ValueError('Candidate version differs from the committed source')


def create(version: str, artifacts: list[Path], allow_dirty: bool = False,
           provenance: dict | None = None) -> dict:
    names = git('ls-files', '-z').split('\0')
    extra = git('ls-files', '--others', '--exclude-standard', '-z').split('\0')
    extra = [name for name in extra if name.startswith(('app/', 'scripts/', 'tests/', '.github/', 'docs/'))
             or name == 'pytest.ini']
    dirty = bool(git('diff', 'HEAD', '--name-only') or extra)
    if dirty and not allow_dirty:
        raise ValueError('Commit candidate sources before building Actions artifacts')
    source_files = {name: digest(ROOT / name) for name in sorted(set(names + extra))
                    if name and (ROOT / name).is_file()}
    entries = []
    for path in artifacts:
        if any(entry['name'] == path.name for entry in entries):
            raise ValueError(f'Duplicate artifact name: {path.name}')
        entries.append({'name': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    if not entries:
        raise ValueError('At least one artifact is required')
    result = {
        'schema_version': 2 if provenance is not None else 1, 'version': version,
        'source': {'commit': git('rev-parse', 'HEAD'), 'dirty': dirty,
                   'tree_sha256': hashlib.sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest(),
                   'files': source_files},
        'build': {'platform': sys.platform, 'python': sys.version,
                  'run_id': os.environ.get('GITHUB_RUN_ID'),
                  'repository': os.environ.get('GITHUB_REPOSITORY')},
        'artifacts': entries,
    }
    if provenance is not None:
        result['provenance'] = provenance
        verify_provenance(result)
    return result


def verify_provenance(manifest: dict) -> None:
    """Keep the evaluated source separate from the actual origin of reused bytes."""
    lineage = manifest.get('provenance', {})
    required = {'quality', 'core', 'ui', 'compile', 'package', 'probe', 'sources'}
    if manifest['build']['platform'] == 'win32':
        required.add('installer')
    if not required <= lineage.keys():
        raise ValueError('Candidate lacks successful stage provenance')
    platform = 'windows' if manifest['build']['platform'] == 'win32' else 'linux'
    for stage, receipt in lineage.items():
        if receipt.get('stage') != stage or receipt.get('status') != 'passed':
            raise ValueError('Invalid stage provenance')
        inputs = receipt['inputs']
        if receipt.get('platform') != platform or inputs.get('platform') != platform:
            raise ValueError('Stage provenance platform mismatch')
        encoded = json.dumps(inputs, sort_keys=True, separators=(',', ':')).encode()
        if hashlib.sha256(encoded).hexdigest() != receipt['fingerprint']:
            raise ValueError('Stage input fingerprint mismatch')
        if receipt['producer']['repository'] != manifest['build']['repository']:
            raise ValueError('Foreign stage provenance')
        if any(manifest['source']['files'].get(name) != checksum
               for name, checksum in inputs['files'].items()):
            raise ValueError(f'Stage {stage} does not match the evaluated source')
        for dependency, files in inputs.get('dependencies', {}).items():
            if dependency not in lineage or any(lineage[dependency]['files'].get(name) != entry
                                                for name, entry in files.items()):
                raise ValueError('Stage provenance dependency mismatch')
    for artifact in manifest.get('artifacts', []):
        if not any(Path(name).name == artifact['name']
                   and entry == {'bytes': artifact['bytes'], 'sha256': artifact['sha256']}
                   for receipt in lineage.values() for name, entry in receipt.get('files', {}).items()):
            raise ValueError('Final bytes are not bound to successful stage provenance')


def verify(manifest: dict, directory: Path, version: str, commit: str, run_id: str) -> None:
    if (manifest.get('schema_version') not in {1, 2} or manifest.get('version') != version
            or manifest['source']['commit'] != commit or manifest['source']['dirty']
            or str(manifest['build']['run_id']) != run_id):
        raise ValueError('Candidate version, commit, clean source or run does not match')
    if manifest['schema_version'] == 2:
        verify_provenance(manifest)
    if not manifest['artifacts']:
        raise ValueError('Empty candidate')
    for entry in manifest['artifacts']:
        name = entry['name']
        if Path(name).name != name or '/' in name or '\\' in name or name in {'.', '..'}:
            raise ValueError('Unsafe artifact name')
        path = directory / name
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f'Candidate checksum mismatch: {name}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--artifact', type=Path, action='append', default=[])
    parser.add_argument('--allow-dirty', action='store_true', help='Local exploratory builds only')
    parser.add_argument('--check-source', action='store_true', help='Verify version without rewriting files')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--commit')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if args.check_source:
        check_source_version(args.version)
    elif args.verify:
        if not args.commit or not args.run_id:
            parser.error('--verify requires --commit and --run-id')
        verify(json.loads(args.verify.read_text(encoding='utf-8')), args.verify.parent,
               args.version, args.commit, args.run_id)
    else:
        if not args.output:
            parser.error('--output is required')
        manifest = create(args.version, args.artifact, args.allow_dirty)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
