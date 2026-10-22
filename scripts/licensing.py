"""Offline technical checks for notices, not a legal compliance certificate."""
from __future__ import annotations

import fnmatch
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import re
import sys

from packaging.requirements import Requirement


class LicenseError(ValueError):
    """A required legal resource is missing, changed or inconsistent."""


def canonical_name(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '\\' in relative or ':' in relative or '..' in parts.parts:
        raise LicenseError(f'Unsafe legal path: {relative}')
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise LicenseError(f'Legal path outside root: {relative}')
    return path


def requirements(root: Path, platform: str) -> dict[str, str]:
    result = {}
    for line in (root / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate({'sys_platform': platform}):
            continue
        pins = [spec.version for spec in requirement.specifier if spec.operator == '==']
        if len(pins) != 1:
            raise LicenseError(f'Expected a pinned runtime requirement: {line}')
        result[canonical_name(requirement.name)] = pins[0]
    if platform == 'linux':
        for line in (root / 'requirements-linux-cpu.txt').read_text(encoding='utf-8').splitlines():
            if '==' in line and not line.lstrip().startswith('#'):
                req = Requirement(line)
                result[canonical_name(req.name)] = next(iter(req.specifier)).version
    return result


def validate_catalog(root: Path, *, check_requirements: bool = True) -> dict:
    catalog = json.loads((root / 'legal/inventory.json').read_text(encoding='utf-8'))
    if catalog.get('schema_version') != 1 or catalog.get('legal_approval') is not False:
        raise LicenseError('Unsupported legal inventory schema')
    files = catalog['files']
    for relative, info in files.items():
        path = checked_path(root, relative)
        if not path.is_file() or digest(path) != info['sha256']:
            raise LicenseError(f'Missing or changed legal resource: {relative}')
    if not {'LICENSE', 'THIRD_PARTY_NOTICES.md'} <= files.keys():
        raise LicenseError('Missing Yagua license or third-party index')
    if check_requirements:
        for platform in ('win32', 'linux'):
            expected = requirements(root, platform)
            actual = {p['name']: p['versions'][platform] for p in catalog['packages']
                      if platform in p['versions']}
            if actual != expected:
                raise LicenseError(f'Legal inventory differs from {platform} runtime pins')
        # New shipped resources require an explicit provenance record, not an inferred license.
        resources = {a['path'] for a in catalog['assets']}
        current = {p.relative_to(root).as_posix() for p in (root / 'assets').rglob('*')
                   if p.is_file() and p.suffix.lower() in {'.ttf', '.otf', '.png', '.ico', '.bmp', '.icns'}}
        if resources != current:
            raise LicenseError(f'Asset provenance inventory differs: {sorted(resources ^ current)}')
    for entry in [*catalog['packages'], *catalog['models'], *catalog['assets'],
                  *catalog['native_families']]:
        if not entry.get('status') or not entry.get('license') or not entry.get('source'):
            raise LicenseError(f'Incomplete provenance entry: {entry}')
        for reference in entry.get('notices', []):
            if reference not in files:
                raise LicenseError(f'Untracked notice: {reference}')
        if 'versions' in entry and not entry.get('notices'):
            raise LicenseError(f'No notice for distribution: {entry["name"]}')
    source_manifest = catalog.get('source_archives_manifest')
    if source_manifest:
        if source_manifest not in files:
            raise LicenseError('Untracked source archive manifest')
        sources = json.loads(checked_path(root, source_manifest).read_text(encoding='utf-8'))
        if sources.get('schema_version') != 1 or sources.get('legal_approval') is not False:
            raise LicenseError('Unsupported source archive manifest')
        packages = {p['name']: p for p in catalog['packages']}
        seen = set()
        for archive in sources['archives']:
            name, relative = archive['name'], archive['path']
            if name in seen or name not in packages or relative not in files:
                raise LicenseError('Duplicate or untracked source archive')
            seen.add(name)
            path = checked_path(root, relative)
            if (set(packages[name]['versions'].values()) != {archive['version']}
                    or digest(path) != archive['sha256']
                    or path.stat().st_size != archive['bytes']
                    or not archive['url'].startswith('https://files.pythonhosted.org/')):
                raise LicenseError(f'Source archive differs from runtime: {name}')
        for archive in sources.get('native_archives', []):
            relative = archive['path']
            if relative not in files:
                raise LicenseError('Untracked native source archive')
            path = checked_path(root, relative)
            if (digest(path) != archive['sha256']
                    or path.stat().st_size != archive['bytes']
                    or not re.fullmatch(r'[0-9a-f]{40}', archive['commit'])
                    or not archive['url'].startswith((
                        'https://codeload.github.com/',
                        'https://bitbucket.org/multicoreware/x265_git/get/'))):
                raise LicenseError(f'Invalid native source archive: {archive["name"]}')
    for asset in catalog['assets']:
        if check_requirements or asset['packaged']:
            path = checked_path(root, asset['path'])
            if not path.is_file() or digest(path) != asset['sha256']:
                raise LicenseError(f'Asset changed since provenance review: {asset["path"]}')
    return catalog


def legal_data(root: Path) -> list[tuple[str, str]]:
    catalog = validate_catalog(root)
    # inventory.json indexes the immutable originals; validate it before packaging.
    paths = [root / name for name in catalog['files']]
    paths += [root / 'legal/inventory.json']
    return [(str(p), p.relative_to(root).parent.as_posix()) for p in paths]


def notice_files(distribution) -> list[tuple[Path, str]]:
    """Include original notices outside dist-info, preserving RECORD paths safely."""
    result = []
    for file in distribution.files or []:
        relative = str(file).replace('\\', '/')
        parts = PurePosixPath(relative).parts
        name = parts[-1].lower()
        in_notices = any(p.lower() in {'licenses', 'licensing'} for p in parts[:-1])
        named = (name.startswith(('license', 'licence', 'copying', 'copyright', 'authors', 'notice'))
                 or ('third' in name and 'party' in name))
        if not (in_notices or named) or Path(name).suffix in {'.py', '.pyc', '.pyd', '.so', '.dll'}:
            continue
        source = Path(distribution.locate_file(file))
        if not source.is_file():
            raise LicenseError(f'Notice recorded but missing: {distribution.metadata["Name"]}/{relative}')
        # RECORD may point at ../Library/share/doc. Keep its structure without escaping legal/.
        safe = PurePosixPath(*('_parent_' if p == '..' else p for p in parts)).as_posix()
        checked_path(Path('.'), safe)
        result.append((source, safe))
    return sorted(result, key=lambda pair: pair[1])


def installed_notices(root: Path, platform: str | None = None, distributions=None) -> tuple[list, dict]:
    catalog = validate_catalog(root)
    platform = platform or ('win32' if sys.platform == 'win32' else 'linux')
    expected = requirements(root, platform)
    lookup = distributions or metadata.distribution
    entries = []
    datas = []
    for name, version in sorted(expected.items()):
        dist = lookup(name)
        if dist.version != version:
            raise LicenseError(f'{name}: expected {version}, installed {dist.version}')
        notices = []
        for source, relative in notice_files(dist):
            destination = f'legal/installed-notices/{name}/{relative}'
            notices.append({'path': destination, 'sha256': digest(source), 'wheel_record': relative})
            datas.append((str(source), PurePosixPath(destination).parent.as_posix()))
        # Some wheels omit their license; the reviewed pinned upstream original is vendored.
        fallback = next(p['notices'] for p in catalog['packages'] if p['name'] == name)
        entries.append({'name': name, 'version': version, 'notices': notices,
                        'catalog_notices': fallback})
    return datas, {'schema_version': 1, 'platform': platform, 'packages': entries,
                   'legal_approval': False,
                   'scope': 'Technical notice/version verification; see legal/REVIEW.md for open obligations.'}


def package_resources(package: Path) -> Path:
    for relative in ('_internal', 'usr/lib/yagua/_internal', '.'):
        candidate = package / relative
        if (candidate / 'legal/inventory.json').is_file():
            return candidate
    raise LicenseError('Packaged legal/inventory.json missing')


def verify_package(package: Path, platform: str) -> dict:
    root = package_resources(package)
    catalog = validate_catalog(root, check_requirements=False)
    report_path = root / 'legal/installed-inventory.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('schema_version') != 1 or report.get('platform') != platform:
        raise LicenseError('Packaged legal inventory platform/schema mismatch')
    expected = {p['name']: p['versions'][platform] for p in catalog['packages']
                if platform in p['versions']}
    actual = {p['name']: p['version'] for p in report['packages']}
    if actual != expected or len(actual) != len(report['packages']):
        raise LicenseError('Packaged distribution versions differ from legal inventory')
    for entry in report['packages']:
        required = next(p['notices'] for p in catalog['packages'] if p['name'] == entry['name'])
        if entry.get('catalog_notices') != required:
            raise LicenseError(f'Packaged notice references differ: {entry["name"]}')
        for file in entry['notices']:
            path = checked_path(root, file['path'])
            if not path.is_file() or digest(path) != file['sha256']:
                raise LicenseError(f'Missing or changed installed notice: {file["path"]}')
    native = []
    for path in sorted(package.rglob('*')):
        if not path.is_file() or not re.search(r'\.(dll|pyd|dylib|so(?:\.[\d]+)*)$', path.name, re.I):
            continue
        relative = path.relative_to(package).as_posix()
        families = [f['id'] for f in catalog['native_families']
                    if any(fnmatch.fnmatch(relative.lower(), pattern) for pattern in f['patterns'])]
        native.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path),
                       'families': families, 'status': 'binary-inventoried-license-review-pending'})
    return {'technical_status': 'passed', 'legal_approval': False, 'platform': platform,
            'packages': report['packages'], 'native_binaries': native,
            'unclassified_native_binaries': [p['path'] for p in native if not p['families']],
            'review_required': catalog['review_required']}


def verify_models(models: Path, catalog: dict) -> list[dict]:
    """Check explicit disposable model directories only; never download weights."""
    result = []
    for model in catalog['models']:
        paths = [p for p in models.rglob(model['name']) if p.is_file()]
        if len(paths) != 1:
            raise LicenseError(f'Model missing or ambiguous: {model["name"]}')
        path = paths[0]
        if path.stat().st_size != model['bytes'] or digest(path) != model['sha256']:
            raise LicenseError(f'Model differs from provenance record: {model["name"]}')
        result.append({'name': model['name'], 'sha256': model['sha256'], 'status': model['status']})
    return result
