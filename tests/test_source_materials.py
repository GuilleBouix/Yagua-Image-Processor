"""Source delivery rejects damaged inputs and never replaces existing outputs."""
import hashlib
import io
import json
import sys
import tarfile

import pytest

from scripts.ci import source_materials
from scripts import licensing


def manifest(name='upstream/example.tar.gz', data=b'original source'):
    return {'schema_version': 1, 'complete_corresponding_source': False,
            'files': [{'file': name, 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest(),
                       'url': 'https://example.org/original.tar.gz'}]}


def test_bundle_preserves_originals_and_records_manifest(tmp_path):
    document = manifest()
    name = document['files'][0]['file']
    path = tmp_path / name
    path.parent.mkdir()
    path.write_bytes(b'original source')
    output = tmp_path / 'materials.tar.xz'
    result = source_materials.collect(document, tmp_path, output)
    assert result['complete_corresponding_source'] is False
    assert result['sha256'] == source_materials.digest(output)
    with tarfile.open(output) as archive:
        assert archive.extractfile(name).read() == path.read_bytes()
        assert json.load(archive.extractfile('materials.json')) == document
    # Stable metadata makes the same inputs produce the same archive on both systems.
    second = source_materials.collect(document, tmp_path, tmp_path / 'again.tar.xz')
    assert second['sha256'] == result['sha256']


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/drive', r'a\b',
                                'a/../b', './local', 'a//b', ''])
def test_reject_unsafe_names(tmp_path, name):
    with pytest.raises(ValueError, match='Unsafe'):
        source_materials.collect(manifest(name), tmp_path, tmp_path / 'out.tar.xz')
    assert not (tmp_path / 'out.tar.xz').exists()


@pytest.mark.parametrize('change', ['hash', 'size', 'missing', 'duplicate', 'claim'])
def test_invalid_inputs_do_not_publish(tmp_path, change):
    document = manifest('original.tar.gz')
    path = tmp_path / 'original.tar.gz'
    path.write_bytes(b'original source')
    if change == 'hash':
        path.write_bytes(b'wrong bytes!!!!')
    elif change == 'size':
        document['files'][0]['bytes'] += 1
    elif change == 'missing':
        path.unlink()
    elif change == 'duplicate':
        document['files'] *= 2
    else:
        document['complete_corresponding_source'] = True
    with pytest.raises((ValueError, FileNotFoundError)):
        source_materials.collect(document, tmp_path, tmp_path / 'out.tar.xz')
    assert not (tmp_path / 'out.tar.xz').exists()


def test_never_replace_existing_output(tmp_path):
    document = manifest('source')
    (tmp_path / 'source').write_bytes(b'original source')
    output = tmp_path / 'existing'
    output.write_bytes(b'keep this')
    with pytest.raises(FileExistsError):
        source_materials.collect(document, tmp_path, output)
    assert output.read_bytes() == b'keep this'
    assert {p.name for p in tmp_path.iterdir()} == {'source', 'existing'}


def test_download_failure_cleans_temporary_files(tmp_path, monkeypatch):
    document = manifest()
    class Response(io.BytesIO):
        url = document['files'][0]['url']
    monkeypatch.setattr(source_materials.urllib.request, 'urlopen',
                        lambda *args, **kwargs: Response(b'wrong source'))
    with pytest.raises(ValueError, match='checksum'):
        source_materials.collect(document, tmp_path, tmp_path / 'out.tar.xz', download=True)
    assert list((tmp_path / 'upstream').iterdir()) == []


def test_no_network_by_default(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail('Network must be explicitly enabled')
    monkeypatch.setattr(source_materials.urllib.request, 'urlopen', unexpected)
    with pytest.raises(FileNotFoundError):
        source_materials.collect(manifest(), tmp_path, tmp_path / 'out.tar.xz')


@pytest.mark.parametrize('failure', [None, 'oversized', 'redirect', 'write'])
def test_download_and_publication_are_atomic(tmp_path, monkeypatch, failure):
    document = manifest()
    data = b'original source' if failure != 'oversized' else b'too many source bytes'
    class Response(io.BytesIO):
        url = 'http://example.org/source' if failure == 'redirect' else document['files'][0]['url']
    monkeypatch.setattr(source_materials.urllib.request, 'urlopen',
                        lambda *args, **kwargs: Response(data))
    if failure == 'write':
        def fail(*args, **kwargs):
            raise OSError('Simulated disk failure')
        monkeypatch.setattr(source_materials.tarfile, 'open', fail)
    output = tmp_path / 'out.tar.xz'
    if failure:
        with pytest.raises((ValueError, OSError)):
            source_materials.collect(document, tmp_path, output, download=True)
        assert not output.exists()
        expected = ['example.tar.gz'] if failure == 'write' else []
        assert sorted(p.name for p in (tmp_path / 'upstream').iterdir()) == expected
    else:
        source_materials.collect(document, tmp_path, output, download=True)
        assert (tmp_path / document['files'][0]['file']).read_bytes() == data
        assert output.exists()
    assert not [p for p in tmp_path.iterdir() if p.name.startswith('tmp')]


def test_repository_notice_inputs_stay_in_root(tmp_path):
    document = manifest('notices/license.txt')
    document['files'][0]['repository_path'] = '../outside'
    with pytest.raises(ValueError, match='Unsafe'):
        source_materials.collect(document, tmp_path, tmp_path / 'out.tar.xz', root=tmp_path)


def test_manifest_tracks_exact_ubuntu_source_versions():
    document = json.loads(source_materials.MANIFEST.read_text(encoding='utf-8'))
    assert len(document['ubuntu_packages']) == 16
    entries = {e['component']: e['version'] for e in document['files'] if 'component' in e}
    for package in document['ubuntu_packages']:
        assert entries[package['source']] == package['version']
    assert len({e['file'] for e in document['files']}) == len(document['files'])


def test_bootstrap_and_system_notices_are_in_frozen_package_inputs():
    included = {str(path) for path, _ in licensing.legal_data(source_materials.ROOT)}
    for relative in ['AppRun-LICENSE.txt', 'AppImageKit-LICENSE.txt',
                     'glibc-copyright.txt', 'gcc-12-copyright.txt',
                     'libxcrypt-copyright.txt', 'zlib-copyright.txt',
                     'AppImage-runtime-header.txt',
                     'squashfuse-1f98030-LICENSE.txt',
                     'squashfuse-1f98030-fuseprivate-header.txt',
                     'xz-runtime-5.2.3-COPYING.txt', 'libvpx-1.15.2-PATENTS.txt',
                     'common-licenses/LGPL-2.1', 'common-licenses/GPL-3']:
        assert str(source_materials.ROOT / 'legal/distribution/notices' / relative) in included


def test_cli_binds_native_report_to_candidate_without_losing_review_baseline(tmp_path, monkeypatch):
    document = manifest('source')
    document['candidate_commit'] = 'a' * 40
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(document))
    native = tmp_path / 'native.json'
    native.write_text(json.dumps({'status': 'passed'}))
    captured = {}
    def collect(document, *args, **kwargs):
        captured.update(document)
        return {'status': 'collected'}
    monkeypatch.setattr(source_materials, 'ROOT', tmp_path)
    monkeypatch.setattr(source_materials, 'collect', collect)
    monkeypatch.setattr(sys, 'argv', ['source_materials', '--manifest', str(path), '--cache', str(tmp_path),
                                 '--output', str(tmp_path / 'out.tar.xz'), '--candidate-commit', 'b' * 40,
                                 '--native-build-report', str(native)])
    assert source_materials.main() == 0
    assert captured['candidate_commit'] == 'b' * 40
    assert captured['review_baseline_commit'] == 'a' * 40
    assert captured['files'][-1]['sha256'] == source_materials.digest(native)
