from pathlib import Path

import pytest
import yaml

from scripts.ci import candidate_manifest as candidate


def test_version_check_preserves_source_bytes_and_rejects_other_version(tmp_path, monkeypatch):
    monkeypatch.setattr(candidate, 'ROOT', tmp_path)
    (tmp_path / 'app').mkdir()
    file = tmp_path / 'app/version.py'
    original = b'# Version\r\n__version__ = "2.0.0"\r\n'
    file.write_bytes(original)
    candidate.check_source_version('2.0.0')
    assert file.read_bytes() == original
    with pytest.raises(ValueError, match='committed source'):
        candidate.check_source_version('2.0.1')
    assert file.read_bytes() == original


def test_candidate_requires_clean_sources_and_records_exact_bytes(tmp_path, monkeypatch):
    source = tmp_path / 'main.py'
    source.write_text('print(1)', encoding='utf-8')
    artifact = tmp_path / 'Yagua.zip'
    artifact.write_bytes(b'candidate')
    monkeypatch.setattr(candidate, 'ROOT', tmp_path)
    def git(*args):
        return {('ls-files', '-z'): 'main.py',
                ('ls-files', '--others', '--exclude-standard', '-z'): '',
                ('diff', 'HEAD', '--name-only'): 'main.py',
                ('rev-parse', 'HEAD'): 'abc123'}[args]
    monkeypatch.setattr(candidate, 'git', git)
    with pytest.raises(ValueError, match='Commit candidate'):
        candidate.create('2.0.0', [artifact])
    manifest = candidate.create('2.0.0', [artifact], allow_dirty=True)
    assert manifest['source']['dirty']
    assert manifest['source']['files']['main.py'] == candidate.digest(source)
    assert manifest['artifacts'] == [{'name': 'Yagua.zip', 'bytes': 9,
                                     'sha256': candidate.digest(artifact)}]
    with pytest.raises(ValueError, match='Duplicate'):
        candidate.create('2.0.0', [artifact, artifact], allow_dirty=True)


def manifest_for(path):
    return {'schema_version': 1, 'version': '2.0.0',
            'source': {'commit': 'abc123', 'dirty': False},
            'build': {'run_id': '123'},
            'artifacts': [{'name': path.name, 'bytes': path.stat().st_size,
                           'sha256': candidate.digest(path)}]}


def test_publication_rejects_changed_file(tmp_path):
    artifact = tmp_path / 'Yagua.zip'
    artifact.write_bytes(b'candidate')
    manifest = manifest_for(artifact)
    candidate.verify(manifest, tmp_path, '2.0.0', 'abc123', '123')
    artifact.write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='checksum'):
        candidate.verify(manifest, tmp_path, '2.0.0', 'abc123', '123')


@pytest.mark.parametrize('field,value', [('version', '2.0.1'), ('commit', 'wrong'),
                                        ('run', '456'), ('dirty', True), ('name', '../Yagua.zip')])
def test_publication_rejects_mismatched_candidate(tmp_path, field, value):
    artifact = tmp_path / 'Yagua.zip'
    artifact.write_bytes(b'candidate')
    manifest = manifest_for(artifact)
    if field == 'version':
        manifest['version'] = value
    elif field in {'commit', 'dirty'}:
        manifest['source'][field] = value
    elif field == 'run':
        manifest['build']['run_id'] = value
    else:
        manifest['artifacts'][0]['name'] = value
    with pytest.raises(ValueError):
        candidate.verify(manifest, tmp_path, '2.0.0', 'abc123', '123')


def test_candidate_workflows_cannot_publish_and_publication_never_builds():
    root = Path(__file__).resolve().parents[1] / '.github/workflows'
    for name in ('build-windows.yml', 'build-linux.yml', 'candidates.yml'):
        text = (root / name).read_text(encoding='utf-8')
        workflow = yaml.load(text, Loader=yaml.BaseLoader)
        assert workflow['permissions'] == {'contents': 'read', 'actions': 'read'}
        assert 'push' not in workflow['on']
        assert 'action-gh-release' not in text and 'contents: write' not in text
        assert 'apply_version.py' not in text
    for name in ('release.yml', 'release-linux.yml'):
        text = (root / name).read_text(encoding='utf-8')
        workflow = yaml.load(text, Loader=yaml.BaseLoader)
        assert set(workflow['on']) == {'workflow_dispatch'}
        assert 'candidate_run_id' in workflow['on']['workflow_dispatch']['inputs']
        assert 'candidate_manifest.py --verify' in text
        assert 'PyInstaller' not in text and 'build-linux' not in text
