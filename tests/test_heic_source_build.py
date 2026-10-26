"""HEIC packaging must retain pinned sources and reject unknown compatibility libraries."""
import hashlib
import io
import json
import tarfile

import pytest

from scripts.ci import build_heic_linux


def test_source_tampering_is_rejected_before_extraction(tmp_path):
    sources = tmp_path / 'legal/sources'
    sources.mkdir(parents=True)
    entries = []
    for name in ['libheif', 'libde265', 'x265', 'pillow-heif']:
        path = sources / f'{name}.tar.gz'
        path.write_bytes(b'not a source archive')
        entries.append({'name': name, 'path': path.relative_to(tmp_path).as_posix(),
                        'bytes': path.stat().st_size, 'sha256': '0' * 64})
    (sources / 'manifest.json').write_text(json.dumps({'archives': entries, 'native_archives': []}))
    work = tmp_path / 'work'
    with pytest.raises(ValueError, match='Changed HEIC source'):
        build_heic_linux.extract_sources(work, tmp_path)
    assert not work.exists()


def test_source_extraction_uses_data_filter(tmp_path):
    sources = tmp_path / 'legal/sources'
    sources.mkdir(parents=True)
    entries = []
    for name in ['libheif', 'libde265', 'x265', 'pillow-heif']:
        path = sources / f'{name}.tar.gz'
        with tarfile.open(path, 'w:gz') as archive:
            member = tarfile.TarInfo('../outside')
            member.size = 1
            archive.addfile(member, io.BytesIO(b'x'))
        entries.append({'name': name, 'path': path.relative_to(tmp_path).as_posix(),
                        'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (sources / 'manifest.json').write_text(json.dumps({'archives': entries, 'native_archives': []}))
    with pytest.raises(tarfile.FilterError):
        build_heic_linux.extract_sources(tmp_path / 'work', tmp_path)
    assert not (tmp_path / 'outside').exists()


def test_no_prebuilt_heic_math_library_survives_packaging(tmp_path):
    package = tmp_path / 'app'
    library = package / 'runtime/compat/pillow_heif.libs/libmvec-2-deadbeef.28.so'
    library.parent.mkdir(parents=True)
    library.write_bytes(b'unknown vendor binary')
    with pytest.raises(ValueError, match='Unidentified prebuilt HEIC'):
        build_heic_linux.check_package(package)
    library.rename(library.with_name('libmvec.so.1'))
    build_heic_linux.check_package(package)


def test_native_build_keeps_prior_results(tmp_path, monkeypatch):
    monkeypatch.setattr(build_heic_linux.sys, 'platform', 'linux')
    monkeypatch.setattr(build_heic_linux.os, 'uname', lambda: type('Uname', (), {'machine': 'x86_64'})(), raising=False)
    work = tmp_path / 'existing'
    work.mkdir()
    original = work / 'keep'
    original.write_bytes(b'keep original experiment')
    with pytest.raises(FileExistsError):
        build_heic_linux.build(work, tmp_path / 'report.json')
    assert original.read_bytes() == b'keep original experiment'


def test_pinned_native_versions_have_not_changed():
    assert build_heic_linux.VERSIONS == {
        'libheif': '1.21.2', 'libde265': '1.0.16', 'x265': '4.1+1-1d117be'}
    assert '-DWITH_X265=ON' in build_heic_linux.HEIF_FLAGS
    assert '-DWITH_LIBDE265=ON' in build_heic_linux.HEIF_FLAGS
