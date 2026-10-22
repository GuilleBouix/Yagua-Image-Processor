"""License-resource regressions use disposable files, never real images/settings."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import sys
from types import ModuleType, SimpleNamespace

import pytest

from scripts import licensing, packaging_rules
from scripts.ci import check_licenses


ROOT = Path(__file__).resolve().parents[1]


def test_source_archives_match_runtime_and_are_packaged():
    catalog = licensing.validate_catalog(ROOT)
    manifest = json.loads((ROOT / catalog['source_archives_manifest']).read_text(encoding='utf-8'))
    assert {a['name'] for a in manifest['archives']} == {
        'certifi', 'tqdm', 'python-bidi', 'shapely', 'pillow-heif'}
    included = {Path(source).relative_to(ROOT).as_posix()
                for source, _ in licensing.legal_data(ROOT)}
    assert {a['path'] for a in manifest['archives']} <= included
    assert {a['name'] for a in manifest['native_archives']} == {
        'libheif', 'libde265', 'geos', 'x265'}
    assert {a['path'] for a in manifest['native_archives']} <= included
    assert {'legal/SOURCE_CODE.md', catalog['source_archives_manifest']} <= included


@pytest.mark.parametrize('change', ['version', 'bytes', 'sha256', 'url', 'duplicate', 'missing'])
def test_source_archive_contract(repository, change):
    root, catalog = repository
    archive = root / 'legal/demo.tar.gz'
    archive.write_bytes(b'disposable source archive')
    entry = dict(name='demo', version='1.0', path='legal/demo.tar.gz',
                 sha256=licensing.digest(archive), bytes=archive.stat().st_size,
                 url='https://files.pythonhosted.org/demo.tar.gz')
    catalog['files'][entry['path']] = {'sha256': entry['sha256']}
    if change == 'duplicate':
        entries = [entry, entry]
    else:
        entries = [entry]
        if change == 'version':
            entry['version'] = '2.0'
        elif change == 'bytes':
            entry['bytes'] += 1
        elif change == 'sha256':
            entry['sha256'] = '0' * 64
        elif change == 'url':
            entry['url'] = 'http://untrusted.example/archive'
        elif change == 'missing':
            archive.unlink()
    manifest = root / 'legal/sources.json'
    manifest.write_text(json.dumps(dict(schema_version=1, legal_approval=False,
                                        archives=entries)), encoding='utf-8')
    catalog['files']['legal/sources.json'] = {'sha256': licensing.digest(manifest)}
    catalog['source_archives_manifest'] = 'legal/sources.json'
    write_catalog(root, catalog)
    with pytest.raises(licensing.LicenseError):
        licensing.validate_catalog(root)


def write_catalog(root, catalog):
    (root / 'legal/inventory.json').write_text(json.dumps(catalog), encoding='utf-8')


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / 'repository'
    (root / 'legal/licenses').mkdir(parents=True)
    files = ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'legal/README.md', 'legal/REVIEW.md',
             'legal/licenses/demo-LICENSE']
    for relative in files:
        (root / relative).write_text('Original notice\n', encoding='utf-8')
    (root / 'requirements.txt').write_text('demo==1.0\n', encoding='utf-8')
    (root / 'requirements-linux-cpu.txt').write_text('# CPU overrides\n', encoding='utf-8')
    catalog = {
        'schema_version': 1, 'legal_approval': False,
        'files': {p: {'sha256': licensing.digest(root / p)} for p in files},
        'packages': [{'name': 'demo', 'versions': {'win32': '1.0', 'linux': '1.0'},
                      'license': 'MIT', 'source': 'https://example.org/demo',
                      'status': 'text-verified', 'notices': ['legal/licenses/demo-LICENSE']}],
        'assets': [], 'models': [], 'native_families': [], 'review_required': ['legal-review'],
    }
    write_catalog(root, catalog)
    return root, catalog


def fake_distribution(tmp_path, version='1.0'):
    wheel = tmp_path / 'wheel'
    notices = ['demo-1.0.dist-info/licenses/LICENSE', 'demo/ThirdPartyNotices.txt',
               '../Library/share/doc/demo/licensing/redistribution.txt']
    for name in notices:
        path = wheel / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'Original {name}\n', encoding='utf-8')
    return SimpleNamespace(version=version, metadata={'Name': 'demo'},
                           files=[PurePosixPath(p) for p in notices + ['demo/__init__.py']],
                           locate_file=lambda path: wheel / str(path))


def make_package(root, tmp_path, platform, distribution):
    datas, report = licensing.installed_notices(root, platform, lambda name: distribution)
    package = tmp_path / 'package'
    relative = '_internal' if platform == 'win32' else 'usr/lib/yagua/_internal'
    resources = package / relative
    for source, destination in licensing.legal_data(root) + datas:
        target = resources / destination / Path(source).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (resources / 'legal/installed-inventory.json').write_text(json.dumps(report), encoding='utf-8')
    return package, resources, report


def test_real_catalog_covers_pins_assets_and_five_models():
    catalog = licensing.validate_catalog(ROOT)
    assert len(catalog['packages']) == 53
    assert len(licensing.requirements(ROOT, 'linux')) == 51
    assert licensing.requirements(ROOT, 'linux')['torch'] == '2.11.0+cpu'
    assert {p['name'] for p in catalog['models']} == {
        'craft_mlt_25k.pth', 'english_g2.pth', 'latin_g2.pth',
        'isnet-general-use.onnx', 'u2netp.onnx',
    }
    assert all(p['notices'] for p in catalog['packages'])
    assert catalog['legal_approval'] is False
    assert 'intel-binary-terms' in catalog['review_required']


@pytest.mark.parametrize('relative', ['LICENSE', 'THIRD_PARTY_NOTICES.md',
                                     'legal/licenses/demo-LICENSE'])
def test_missing_required_original_fails(repository, relative):
    root, _ = repository
    (root / relative).unlink()
    with pytest.raises(licensing.LicenseError, match='Missing or changed'):
        licensing.validate_catalog(root)


def test_changed_license_fails(repository):
    root, _ = repository
    (root / 'legal/licenses/demo-LICENSE').write_text('Changed notice')
    with pytest.raises(licensing.LicenseError, match='Missing or changed'):
        licensing.validate_catalog(root)


@pytest.mark.parametrize('platform', ['win32', 'linux'])
def test_dependency_upgrade_requires_inventory_update(repository, platform):
    root, catalog = repository
    catalog['packages'][0]['versions'][platform] = '2.0'
    write_catalog(root, catalog)
    with pytest.raises(licensing.LicenseError, match='runtime pins'):
        licensing.validate_catalog(root)


def test_new_asset_requires_provenance(repository):
    root, _ = repository
    (root / 'assets').mkdir()
    (root / 'assets/new.png').write_bytes(b'image')
    with pytest.raises(licensing.LicenseError, match='provenance inventory'):
        licensing.validate_catalog(root)


@pytest.mark.parametrize('relative', ['../secret', '/absolute', 'C:/secret', 'a\\b'])
def test_legal_paths_cannot_escape_checkout(tmp_path, relative):
    with pytest.raises(licensing.LicenseError):
        licensing.checked_path(tmp_path, relative)


def test_runtime_notices_include_external_originals_without_path_escape(repository, tmp_path):
    root, _ = repository
    dist = fake_distribution(tmp_path)
    datas, report = licensing.installed_notices(root, 'win32', lambda name: dist)
    assert len(datas) == 3
    assert any('ThirdPartyNotices.txt' in n['path'] for n in report['packages'][0]['notices'])
    assert any('_parent_/Library' in dest for _, dest in datas)
    assert all('..' not in PurePosixPath(dest).parts for _, dest in datas)
    assert report['legal_approval'] is False


def test_wrong_installed_version_fails(repository, tmp_path):
    root, _ = repository
    with pytest.raises(licensing.LicenseError, match='expected 1.0, installed 2.0'):
        licensing.installed_notices(root, 'win32', lambda name: fake_distribution(tmp_path, '2.0'))


def test_recorded_but_missing_wheel_notice_fails(tmp_path):
    dist = fake_distribution(tmp_path)
    Path(dist.locate_file(dist.files[0])).unlink()
    with pytest.raises(licensing.LicenseError, match='recorded but missing'):
        licensing.notice_files(dist)


@pytest.mark.parametrize('platform', ['win32', 'linux'])
def test_packaged_resources_and_actual_native_inventory(repository, tmp_path, platform):
    root, _ = repository
    package, resources, _ = make_package(root, tmp_path, platform, fake_distribution(tmp_path))
    binary = resources / ('demo.dll' if platform == 'win32' else 'libdemo.so.1')
    binary.write_bytes(b'native-library')
    report = licensing.verify_package(package, platform)
    assert report['technical_status'] == 'passed'
    assert report['legal_approval'] is False
    assert report['native_binaries'][0]['sha256'] == hashlib.sha256(b'native-library').hexdigest()
    assert report['unclassified_native_binaries'] == [binary.relative_to(package).as_posix()]


@pytest.mark.parametrize('mutation', ['missing-original', 'missing-runtime-notice',
                                     'changed-notice', 'wrong-version', 'wrong-platform'])
def test_frozen_package_detects_deliberate_faults(repository, tmp_path, mutation):
    root, _ = repository
    package, resources, report = make_package(root, tmp_path, 'win32', fake_distribution(tmp_path))
    runtime = resources / report['packages'][0]['notices'][0]['path']
    if mutation == 'missing-original':
        (resources / 'LICENSE').unlink()
    elif mutation == 'missing-runtime-notice':
        runtime.unlink()
    elif mutation == 'changed-notice':
        runtime.write_bytes(b'changed')
    else:
        if mutation == 'wrong-version':
            report['packages'][0]['version'] = '2.0'
        else:
            report['platform'] = 'linux'
        (resources / 'legal/installed-inventory.json').write_text(json.dumps(report))
    with pytest.raises(licensing.LicenseError):
        licensing.verify_package(package, 'win32')


def test_cli_returns_failure_when_license_is_missing(repository, capsys):
    root, _ = repository
    (root / 'LICENSE').unlink()
    assert check_licenses.main(['--root', str(root)]) == 1
    assert 'Legal resource check failed' in capsys.readouterr().err


def test_model_provenance_checks_no_downloads_or_real_profiles(repository, tmp_path):
    _, catalog = repository
    models = tmp_path / 'models'
    models.mkdir()
    file = models / 'demo.onnx'
    file.write_bytes(b'model')
    catalog['models'] = [{'name': file.name, 'bytes': 5, 'sha256': licensing.digest(file),
                          'status': 'permission-review-pending'}]
    assert licensing.verify_models(models, catalog)[0]['status'] == 'permission-review-pending'
    file.write_bytes(b'wrong')
    with pytest.raises(licensing.LicenseError, match='differs'):
        licensing.verify_models(models, catalog)


def test_absent_model_fails(repository, tmp_path):
    _, catalog = repository
    catalog['models'] = [{'name': 'missing.onnx', 'bytes': 1, 'sha256': '0' * 64}]
    with pytest.raises(licensing.LicenseError, match='missing or ambiguous'):
        licensing.verify_models(tmp_path, catalog)


def test_original_checksums_are_not_changed_by_git_line_endings():
    attributes = (ROOT / '.gitattributes').read_text()
    for rule in ['legal/licenses/** -text', 'LICENSE text eol=lf',
                 'THIRD_PARTY_NOTICES.md text eol=lf', 'legal/*.json text eol=lf']:
        assert rule in attributes


def test_build_inputs_include_notice_index_and_generated_runtime_manifest(repository, tmp_path, monkeypatch):
    # CI deliberately installs runtime + dev requirements, never build tools.
    hooks = ModuleType('PyInstaller.utils.hooks')
    hooks.collect_data_files = lambda name: []
    hooks.copy_metadata = lambda name: []
    for name in ('PyInstaller', 'PyInstaller.utils'):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    monkeypatch.setitem(sys.modules, 'PyInstaller.utils.hooks', hooks)
    root, _ = repository
    dist = fake_distribution(tmp_path)
    monkeypatch.setattr(packaging_rules, 'assert_clean_environment', lambda: None)
    monkeypatch.setattr(packaging_rules, 'runtime_distributions', lambda root: ['demo'])
    monkeypatch.setattr(packaging_rules.importlib.metadata, 'distribution', lambda name: dist)
    inputs = packaging_rules.build_inputs(root)
    names = {Path(source).name for source, _ in inputs['datas']}
    assert {'LICENSE', 'THIRD_PARTY_NOTICES.md', 'installed-inventory.json',
            'ThirdPartyNotices.txt'} <= names
    report_path = next(Path(source) for source, _ in inputs['datas'] if Path(source).name == 'installed-inventory.json')
    report = json.loads(report_path.read_text())
    assert report['packages'][0]['version'] == '1.0'
    assert report['legal_approval'] is False
