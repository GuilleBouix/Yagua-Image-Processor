"""Collect hash-pinned source materials without extracting or executing archives.

This produces review materials, not a certificate of corresponding-source completeness.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'legal/distribution/materials.json'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root: Path, name: str) -> Path:
    parts = PurePosixPath(name)
    if (not name or parts.is_absolute() or '\\' in name or ':' in name
            or '..' in parts.parts or parts.as_posix() != name):
        raise ValueError(f'Unsafe material path: {name}')
    result = root / name
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Material outside directory: {name}')
    return result


def verify(path: Path, entry: dict) -> None:
    if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
        raise ValueError(f'Material checksum mismatch: {entry["file"]}')


def collect(manifest: dict, cache: Path, output: Path, *, root: Path = ROOT,
            download: bool = False) -> dict:
    """Publish an archive atomically only after verifying every input.

    Existing outputs are never replaced. Downloads go to temporary cache files;
    interrupted or invalid downloads cannot become verified inputs.
    """
    if manifest.get('schema_version') != 1 or manifest.get('complete_corresponding_source') is not False:
        raise ValueError('Unsupported or misleading source-materials manifest')
    inputs = []
    names = set()
    for entry in manifest['files']:
        name = entry['file']
        safe_path(Path('.'), name)
        if name in names or name == 'materials.json':
            raise ValueError(f'Duplicate or reserved material name: {name}')
        names.add(name)
        if 'repository_path' in entry:
            path = safe_path(root, entry['repository_path'])
        else:
            path = safe_path(cache, name)
            if not path.exists() and download:
                url = entry['url']
                if not url.startswith('https://'):
                    raise ValueError(f'HTTPS required: {name}')
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    try:
                        with urllib.request.urlopen(url, timeout=120) as response:
                            if not response.url.startswith('https://'):
                                raise ValueError('Insecure source redirect')
                            while block := response.read(1024 * 1024):
                                stream.write(block)
                                if stream.tell() > entry['bytes']:
                                    raise ValueError(f'Oversized download: {name}')
                    except BaseException:
                        stream.close()
                        temporary.unlink(missing_ok=True)
                        raise
                try:
                    verify(temporary, entry)
                    # Exclusive publication also avoids replacing a concurrent writer.
                    path.hardlink_to(temporary)
                finally:
                    temporary.unlink(missing_ok=True)
        verify(path, entry)
        inputs.append((name, path))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with tarfile.open(temporary, 'w:xz') as archive:
            encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode()
            header = tarfile.TarInfo('materials.json')
            header.size = len(encoded)
            header.mode = 0o644
            archive.addfile(header, io.BytesIO(encoded))
            for name, path in sorted(inputs):
                header = tarfile.TarInfo(name)
                header.size = path.stat().st_size
                header.mode = 0o644
                with path.open('rb') as source:
                    archive.addfile(header, source)
        output.hardlink_to(temporary)
    finally:
        temporary.unlink(missing_ok=True)
    return {'file': output.name, 'bytes': output.stat().st_size,
            'sha256': digest(output), 'materials': len(inputs),
            'complete_corresponding_source': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--candidate-commit')
    parser.add_argument('--native-build-report', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    if args.candidate_commit:
        if not re.fullmatch('[0-9a-f]{40}', args.candidate_commit):
            parser.error('--candidate-commit must be a full Git commit')
        manifest['review_baseline_commit'] = manifest['candidate_commit']
        manifest['candidate_commit'] = args.candidate_commit
    if args.native_build_report:
        path = args.native_build_report.resolve()
        if not path.is_relative_to(ROOT) or json.loads(path.read_text(encoding='utf-8')).get('status') != 'passed':
            parser.error('A passed native build report inside the checkout is required')
        manifest['files'].append({
            'file': 'native-build/linux-heic-native.json',
            'repository_path': path.relative_to(ROOT).as_posix(),
            'bytes': path.stat().st_size, 'sha256': digest(path),
        })
    result = collect(manifest, args.cache, args.output, download=args.download)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
