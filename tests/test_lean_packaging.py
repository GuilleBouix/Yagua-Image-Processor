from pathlib import Path

import pytest

from scripts import packaging_rules
from scripts.ci import check_installed_size
from app.utils import package_selftest

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_have_no_build_test_or_unused_extras():
    runtime = (ROOT / 'requirements.txt').read_text()
    assert 'opencv-python-headless==4.13.0.92' in runtime
    names = {line.split('==')[0].lower() for line in runtime.splitlines() if '==' in line}
    assert not names.intersection({'pandas', 'pytest', 'coverage', 'pyinstaller', 'tkinterdnd2', 'opencv-python'})
    assert {'torch', 'torchvision', 'onnxruntime', 'numpy', 'scipy', 'numba', 'pymatting'} <= names


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
    assert not report['within_budget']


def test_size_check_rejects_overlapping_components(tmp_path):
    child = tmp_path / 'models'
    child.mkdir()
    with pytest.raises(ValueError, match='non-overlapping'):
        check_installed_size.measure(tmp_path, child, tmp_path, tmp_path)


def test_all_image_codecs_and_metadata_work_without_video(tmp_path):
    assert package_selftest._verify_image_formats(tmp_path) == [
        'JPEG', 'PNG', 'WEBP', 'AVIF', 'HEIC', 'ICO', 'BMP', 'TIFF', 'GIF',
    ]


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
