import copy
import hashlib
import json
from pathlib import Path
import zipfile

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


def test_all_new_workflows_are_read_only_and_fixture_cannot_publish():
    root = Path(__file__).resolve().parents[1] / '.github/workflows'
    for name in ('stage.yml', 'validation.yml', 'checkpoint-selftest.yml'):
        text = (root / name).read_text()
        assert 'contents: write' not in text and 'action-gh-release' not in text
    assert 'windows-validated' not in (root / 'checkpoint-selftest.yml').read_text()
