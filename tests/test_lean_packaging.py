from pathlib import Path

import pytest

from scripts import packaging_rules
from scripts.ci import check_installed_size
from scripts.ci.audit_frozen import audit
from scripts.ci import audit_frozen
from scripts.ci.probe_package import model_manifest
from scripts.ci import probe_package
from app.utils import package_selftest

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_have_no_build_test_or_unused_extras():
    runtime = (ROOT / 'requirements.txt').read_text()
    assert 'opencv-python-headless==4.13.0.92' in runtime
    names = {line.split('==')[0].lower() for line in runtime.splitlines() if '==' in line}
    assert not names.intersection({'pandas', 'pytest', 'coverage', 'pyinstaller', 'tkinterdnd2', 'opencv-python'})
    assert {'torch', 'torchvision', 'onnxruntime', 'numpy', 'scipy', 'numba', 'pymatting'} <= names


@pytest.mark.parametrize('platform, count, has_tbb', [('win32', 53, True), ('linux', 51, False)])
def test_runtime_metadata_honors_native_windows_dependency_markers(platform, count, has_tbb):
    names = packaging_rules.runtime_distributions(ROOT, {'sys_platform': platform})
    assert len(names) == count
    assert ('tbb' in names) == has_tbb
    assert ('tcmlib' in names) == has_tbb


def test_assets_preserve_runtime_font_and_icons_without_installer_or_macos():
    assets = packaging_rules.runtime_assets(ROOT)
    names = {Path(source).name for source, _ in assets}
    assert {'Inter.ttf', 'icon.ico', 'icon.png', 'ocr.png'} <= names
    assert not names.intersection(packaging_rules.INSTALLER_ASSETS)
    assert not any(source.endswith('.icns') for source, _ in assets)
    assert all(Path(source).is_file() for source, _ in assets)


def test_dynamic_registry_modules_are_included_without_importing_ui():
    modules = packaging_rules.application_modules(ROOT)
    assert 'app.ui.frames.ocr.frame' in modules
    assert 'app.ui.frames.metadata.frame' in modules
    assert 'app.translations.es' in modules
    assert all(not name.endswith('.__init__') for name in modules)


def test_packaging_rejects_a_test_or_editor_environment(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(packaging_rules.importlib.metadata, 'distributions', lambda: [
        SimpleNamespace(metadata={'Name': 'pytest'}),
        SimpleNamespace(metadata={'Name': 'opencv-python'}),
    ])
    with pytest.raises(RuntimeError, match='new venv'):
        packaging_rules.assert_clean_environment()


@pytest.mark.parametrize('destination', [
    'torch/bin/test_api', 'torch/bin/test_jit', 'torch/bin/test_lazy',
    'torch/bin/protoc', 'torch/bin/protoc-3.13.0.0', 'torch\\bin\\protoc.exe',
    'torch/bin/HashStoreTest', 'torch/bin/FileStoreTest', 'torch/bin/TCPStoreTest',
    'cv2/opencv_videoio_ffmpeg4130_64.dll',
])
def test_omit_developer_executables_and_video_plugin(destination):
    assert packaging_rules.omit_packaged_file(destination)


@pytest.mark.parametrize('destination', [
    'torch/bin/torch_shm_manager', 'torch/lib/libtorch_cpu.so',
    'torch/bin/test_runtime.dll', 'torch/bin/test_runtime.so',
    'torch/lib/libtorch_python.so', 'torch/lib/torch_cpu.dll',
    'scipy/optimize/_highspy/_core.cpython-313-x86_64-linux-gnu.so',
    'opencv_python_headless.libs/libavcodec-156beeea.so.62.11.100',
])
def test_keep_runtime_native_libraries_and_torch_shared_memory_manager(destination):
    assert not packaging_rules.omit_packaged_file(destination)


def test_total_budget_counts_models_and_caches_not_only_app(tmp_path, monkeypatch):
    roots = [tmp_path / name for name in ('app', 'models', 'caches')]
    for root in roots:
        root.mkdir()
        (root / 'data').write_bytes(b'1234')
    compressed = tmp_path / 'download.zip'
    compressed.write_bytes(b'12')
    monkeypatch.setattr(check_installed_size, 'within_budget', lambda size: size < 10)
    report = check_installed_size.measure(*roots, compressed)
    assert report['installed_bytes'] == 12
    assert report['compressed_bytes'] == 2
    assert sum(report['app_groups_bytes'].values()) == 4
    assert not report['within_budget']


def test_size_check_rejects_overlapping_components(tmp_path):
    child = tmp_path / 'models'
    child.mkdir()
    with pytest.raises(ValueError, match='non-overlapping'):
        check_installed_size.measure(tmp_path, child, tmp_path, tmp_path)


def test_installed_size_cli_rejects_total_at_limit_without_large_files(tmp_path, monkeypatch):
    roots = {name: tmp_path / name for name in ('app', 'models', 'caches')}
    for root in roots.values():
        root.mkdir()
    compressed = tmp_path / 'download.zip'
    compressed.write_bytes(b'zip')
    sizes = {roots['app']: check_installed_size.MAX_BYTES - 500_000_000, roots['models']: 499_999_999,
             roots['caches']: 1, compressed: 3}
    monkeypatch.setattr(check_installed_size, 'artifact_size', lambda path: sizes[path])
    args = [item for name, root in roots.items() for item in (f'--{name}', str(root))]
    args += ['--compressed', str(compressed), '--report', str(tmp_path / 'report.json')]
    assert check_installed_size.main(args) == 1
    sizes[roots['caches']] = 0
    assert check_installed_size.main(args) == 0


def test_model_manifest_detects_changed_content_even_at_same_size(tmp_path):
    model = tmp_path / 'model.onnx'
    model.write_bytes(b'abc')
    before = model_manifest(tmp_path)
    model.write_bytes(b'xyz')
    after = model_manifest(tmp_path)
    assert before['model.onnx']['bytes'] == after['model.onnx']['bytes']
    assert before['model.onnx']['sha256'] != after['model.onnx']['sha256']


def test_probe_isolates_home_fonts_preferences_and_temp_only_in_child(tmp_path, monkeypatch):
    import json
    import os
    from types import SimpleNamespace

    original_home = os.environ.get('HOME')
    root = tmp_path / 'probe'
    captured = {}

    def process(*args, **kwargs):
        captured.update(kwargs['env'])
        Path(captured['YAGUA_PACKAGE_SELFTEST']).write_text(json.dumps({'status': 'passed'}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(probe_package.subprocess, 'run', process)
    probe_package.run(tmp_path / 'fake-executable', root, 'online', 'preflight')
    for key in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMPDIR', 'XDG_CACHE_HOME'):
        assert Path(captured[key]).is_relative_to(root / 'caches')
    assert os.environ.get('HOME') == original_home


def test_all_image_codecs_and_metadata_work_without_video(tmp_path):
    observations = {}
    assert package_selftest._verify_image_formats(tmp_path, observations) == [
        'JPEG', 'PNG', 'WEBP', 'AVIF', 'HEIC', 'ICO', 'BMP', 'TIFF', 'GIF',
    ]
    assert len(observations) == 9
    assert all(len(item['pixel_sha256']) == 64 for item in observations.values())


def test_stage_records_time_and_memory_on_failure():
    result = {}

    def fail():
        raise ValueError('simulated')

    with pytest.raises(ValueError, match='simulated'):
        package_selftest._stage(result, 'failure', fail)
    stage = result['stages'][0]
    assert stage['status'] == 'failed'
    assert stage['seconds'] >= 0
    assert stage['peak_rss_bytes'] > 0


def test_frozen_audit_rejects_optional_cli_and_wrong_language_data(tmp_path):
    work = tmp_path / 'work'
    work.mkdir()
    (work / 'PYZ-00.toc').write_text(repr(('archive', [('rembg.cli', 'cli.py', 'PYMODULE')])))
    package = tmp_path / 'package'
    characters = package / 'easyocr/character'
    characters.mkdir(parents=True)
    (characters / 'kn.txt').write_text('unused')
    with pytest.raises(RuntimeError, match='rembg.cli'):
        audit(package, work)
    result = audit(package, work, enforce=False)
    assert result['forbidden_modules'] == ['rembg.cli']
    assert result['ocr_characters'] == ['kn.txt']


def test_frozen_audit_accepts_api_and_current_ocr_resources(tmp_path):
    (tmp_path / 'PYZ-00.toc').write_text(repr(('archive', [
        ('rembg.sessions.u2netp', 'session.py', 'PYMODULE'),
        ('easyocr.model.vgg_model', 'model.py', 'PYMODULE'),
    ])))
    package = tmp_path / 'package'
    characters = package / 'easyocr/character'
    characters.mkdir(parents=True)
    for language in ('en', 'es'):
        (characters / f'{language}_char.txt').write_text(language)
    assert audit(package, tmp_path)['forbidden_modules'] == []


def test_frozen_audit_rejects_torch_developer_programs(tmp_path):
    (tmp_path / 'PYZ-00.toc').write_text(repr(('archive', [])))
    package = tmp_path / 'package'
    characters = package / 'easyocr/character'
    characters.mkdir(parents=True)
    for language in ('en', 'es'):
        (characters / f'{language}_char.txt').write_text(language)
    program = package / 'torch/bin/protoc'
    program.parent.mkdir(parents=True)
    program.write_bytes(b'developer executable')
    with pytest.raises(RuntimeError, match='developer_executables'):
        audit(package, tmp_path)


def test_native_audit_reads_dependencies_without_deleting_files(tmp_path, monkeypatch):
    from types import SimpleNamespace

    binary = tmp_path / 'cv2.so'
    binary.write_bytes(b'\x7fELF-not-a-real-image')
    (tmp_path / 'font.ttf').write_bytes(b'font')
    monkeypatch.setattr(audit_frozen.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(
        stdout='0x0000000000000001 (NEEDED) Shared library: [libstdc++.so.6]\n'
               '0x0000000000000001 (NEEDED) Shared library: [libgomp.so.1]\n',
    ))
    assert audit_frozen.elf_dependencies(tmp_path) == {'cv2.so': ['libstdc++.so.6', 'libgomp.so.1']}
    assert binary.read_bytes() == b'\x7fELF-not-a-real-image'


@pytest.mark.parametrize('mutation', [None, 'image_roundtrips', 'background_roundtrips', 'numba_threading_layer'])
def test_comparison_rejects_changed_pixels_or_numba_backend(tmp_path, monkeypatch, mutation):
    import json
    import sys
    from scripts.ci import validate_lean_runtime

    def validate(label, base_ref, reports):
        folder = reports / label
        folder.mkdir()
        probe = {'image_roundtrips': {'PNG': 'pixels'},
                 'background_roundtrips': {'ISNet': 'pixels'}, 'numba_threading_layer': 'tbb'}
        if label == 'candidate' and mutation:
            probe[mutation] = 'changed'
        (folder / 'offline.json').write_text(json.dumps(probe))
        return {'within_budget': True, 'installed_bytes': 10}

    monkeypatch.setattr(validate_lean_runtime, 'validate', validate)
    monkeypatch.setattr(sys, 'argv', ['validate', '--reports', str(tmp_path / 'reports')])
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    assert validate_lean_runtime.main() == (1 if mutation else 0)


def test_positive_savings_do_not_bypass_absolute_size_limit(tmp_path, monkeypatch, capsys):
    from scripts.ci import validate_lean_runtime

    result = {'baseline': {}, 'candidate': {'installed_bytes': 150, 'limit_bytes': 100, 'within_budget': False},
              'saved_bytes': 50, 'image_contract_matches': True, 'background_contract_matches': True,
              'numba_threading_matches': True}
    job_summary = tmp_path / 'github-summary.md'
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(job_summary))

    assert not validate_lean_runtime.write_summary(result, tmp_path)
    assert result['failed_checks'] == ['installed-size']
    assert 'reduce by at least 51 bytes' in capsys.readouterr().err
    assert 'Positive means smaller than baseline' in job_summary.read_text()
    assert (tmp_path / 'summary.md').is_file()


def test_current_linux_size_uses_shared_two_gb_budget_in_summary():
    from scripts.ci.check_linux_size import MAX_BYTES, within_budget
    from scripts.ci.validate_lean_runtime import comparison_checks

    total = 1_527_547_135
    result = {'baseline': {}, 'candidate': {'installed_bytes': total, 'within_budget': within_budget(total)}}
    size_check = next(check for check in comparison_checks(result) if check['name'] == 'installed-size')
    assert size_check['status'] == 'passed'
    assert f'required: < {MAX_BYTES:,} bytes' in size_check['detail']


def test_failed_baseline_reports_skipped_comparisons(tmp_path, monkeypatch):
    from scripts.ci import validate_lean_runtime

    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    result = {'baseline': {'error': 'Native import failed'},
              'candidate': {'installed_bytes': 10, 'within_budget': True}}
    assert not validate_lean_runtime.write_summary(result, tmp_path)
    assert result['failed_checks'] == ['baseline-package']
    assert {item['name'] for item in result['checks'] if item['status'] == 'skipped'} == {
        'image-pixels', 'background-pixels', 'numba-backend',
    }
