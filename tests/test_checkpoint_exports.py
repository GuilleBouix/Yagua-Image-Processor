"""Pruebas de regresión para checkpoint exports y sus contratos asociados."""

import copy
import hashlib
import json
from pathlib import Path
import zipfile
from types import SimpleNamespace

import pytest

from scripts.ci import candidate_manifest as candidate
from scripts.ci.checkpoints import encoded_hash
from scripts.ci.final_exports import verify_export


def modern_manifest():
    manifest = {'schema_version': 2, 'source': {'files': {'app/main.py': 'source'}},
                'build': {'platform': 'win32', 'repository': 'owner/yagua'}}
    lineage = {}
    for stage in ('quality', 'core', 'ui', 'compile', 'package', 'probe', 'sources', 'installer'):
        inputs = {'files': {'app/main.py': 'source'}, 'platform': 'windows'}
        lineage[stage] = {'stage': stage, 'platform': 'windows', 'status': 'passed', 'inputs': inputs,
                          'fingerprint': encoded_hash(inputs),
                          'producer': {'repository': 'owner/yagua', 'commit': 'original', 'run_id': '100'}}
    manifest['provenance'] = lineage
    return manifest


@pytest.mark.parametrize('mutation', ['missing', 'source', 'fingerprint', 'repository', 'failed'])
def test_modern_manifest_rejects_invalid_or_incomplete_provenance(mutation):
    manifest = modern_manifest()
    candidate.verify_provenance(manifest)
    if mutation == 'missing':
        del manifest['provenance']['probe']
    elif mutation == 'source':
        manifest['source']['files']['app/main.py'] = 'new-code'
    elif mutation == 'fingerprint':
        manifest['provenance']['compile']['fingerprint'] = 'forged'
    elif mutation == 'repository':
        manifest['provenance']['compile']['producer']['repository'] = 'foreign/repo'
    else:
        manifest['provenance']['compile']['status'] = 'failed'
    with pytest.raises(ValueError):
        candidate.verify_provenance(manifest)


def test_immutable_export_can_be_retried_without_replacing_it(tmp_path):
    data = b'validated installer'
    manifest = {'artifacts': [{'name': 'setup.exe', 'bytes': len(data),
                               'sha256': hashlib.sha256(data).hexdigest()}]}
    archive = tmp_path / 'export.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('installer/setup.exe', data)
        zipped.writestr('installer/candidate-windows.json', json.dumps(manifest))
    original = archive.read_bytes()
    verify_export(archive, 'installer/candidate-windows.json', manifest)
    assert archive.read_bytes() == original
    changed = copy.deepcopy(manifest)
    changed['artifacts'][0]['sha256'] = 'changed'
    with pytest.raises(ValueError, match='differs'):
        verify_export(archive, 'installer/candidate-windows.json', changed)


def test_immutable_export_verifies_binaries_as_well_as_manifest(tmp_path):
    manifest = {'artifacts': [{'name': 'setup.exe', 'bytes': 4, 'sha256': 'bad'}]}
    archive = tmp_path / 'export.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('setup.exe', b'bad!')
        zipped.writestr('candidate.json', json.dumps(manifest))
    with pytest.raises(ValueError, match='checksum'):
        verify_export(archive, 'candidate.json', manifest)


@pytest.mark.parametrize('prefix', ['', 'reports/'])
def test_source_exports_support_both_actual_upload_artifact_roots(tmp_path, prefix):
    data = b'source archive'
    manifest = {'artifacts': [{'name': 'sources.tar.xz', 'bytes': len(data),
                               'sha256': hashlib.sha256(data).hexdigest()}]}
    archive = tmp_path / 'export.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr(prefix + 'sources.tar.xz', data)
        zipped.writestr(prefix + 'candidate-linux-sources.json', json.dumps(manifest))
    verify_export(archive, 'candidate-linux-sources.json', manifest)


def test_ambiguous_source_manifest_does_not_select_an_arbitrary_copy(tmp_path):
    archive = tmp_path / 'export.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('candidate-linux-sources.json', '{}')
        zipped.writestr('reports/candidate-linux-sources.json', '{}')
    with pytest.raises(ValueError, match='ambiguous'):
        verify_export(archive, 'candidate-linux-sources.json', {})


def test_v2_round_trip_preserves_original_binary_producer_after_new_commit(tmp_path, monkeypatch):
    source = tmp_path / 'app/main.py'
    source.parent.mkdir()
    source.write_text('unchanged app')
    binary = tmp_path / 'setup.exe'
    binary.write_bytes(b'original compiled bytes')
    monkeypatch.setattr(candidate, 'ROOT', tmp_path)
    monkeypatch.setattr(candidate, 'sys', SimpleNamespace(platform='win32', version='3.13.12'))
    monkeypatch.setattr(candidate, 'git', lambda *args: 'new-evaluation-commit' if args[0] == 'rev-parse'
                        else 'app/main.py' if args == ('ls-files', '-z') else '')
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/yagua')
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    lineage = modern_manifest()['provenance']
    for receipt in lineage.values():
        receipt['inputs']['files']['app/main.py'] = candidate.digest(source)
        receipt['fingerprint'] = encoded_hash(receipt['inputs'])
    lineage['package']['files'] = {'installer/setup.exe': {'bytes': binary.stat().st_size,
                                                         'sha256': candidate.digest(binary)}}
    manifest = candidate.create('2.0.0', [binary], provenance=lineage)
    candidate.verify(manifest, tmp_path, '2.0.0', 'new-evaluation-commit', '200')
    assert manifest['build']['run_id'] == '200'
    assert manifest['provenance']['compile']['producer']['run_id'] == '100'
    assert manifest['provenance']['compile']['producer']['commit'] == 'original'


def test_all_new_workflows_are_read_only_and_fixture_cannot_publish():
    root = Path(__file__).resolve().parents[1] / '.github/workflows'
    for name in ('stage.yml', 'validation.yml', 'checkpoint-selftest.yml'):
        text = (root / name).read_text()
        assert 'contents: write' not in text and 'action-gh-release' not in text
    assert 'windows-validated' not in (root / 'checkpoint-selftest.yml').read_text()


def test_installer_diagnostics_do_not_copy_installed_payload(tmp_path, monkeypatch):
    from scripts.ci.stages import installer
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path / 'temporary'))
    monkeypatch.setattr(installer, 'ROOT', tmp_path)
    monkeypatch.setattr(installer, 'save', lambda *_: None)
    def fake_installer(*_):
        work = tmp_path / 'temporary/yagua-installer-finish'
        (work / 'installed-spanish').mkdir(parents=True)
        (work / 'installed-spanish/large-runtime.dll').write_bytes(b'fake-runtime')
        (work / 'setup-spanish.log').write_text('Opened thank-you page')
    monkeypatch.setattr(installer, 'run', fake_installer)
    installer.main()
    assert (tmp_path / 'reports/installer-finish/setup-spanish.log').exists()
    assert not (tmp_path / 'reports/installer-finish/installed-spanish').exists()
