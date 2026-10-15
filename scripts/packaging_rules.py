"""Shared PyInstaller policy for Windows and Linux (no application imports)."""

from pathlib import Path
import importlib.metadata

EXCLUDES = [
    'pandas', 'pytest', '_pytest', 'pytest_cov', 'coverage', 'tkinterdnd2',
    'rembg.cli', 'rembg.commands', 'rembg.__main__', 'torchaudio', 'triton', 'IPython',
    'matplotlib', 'notebook', 'jupyter',
]
INSTALLER_ASSETS = {'installer_icon.ico', 'wizard_image.bmp', 'wizard_small.bmp'}
OCR_LANGUAGES = ['en', 'es']


def assert_clean_environment() -> None:
    forbidden = {'pandas', 'pytest', 'pytest-cov', 'coverage', 'tkinterdnd2', 'opencv-python'}
    installed = {str(dist.metadata.get('Name') or '').lower().replace('_', '-')
                 for dist in importlib.metadata.distributions()}
    unexpected = sorted(installed & forbidden)
    if unexpected:
        raise RuntimeError(
            f'Build environment contains {unexpected}. Use a new venv with runtime + build requirements.'
        )


def omit_packaged_file(destination: str) -> bool:
    """Omit named developer executables, never Torch/SciPy runtime libraries."""
    path = Path(destination.replace('\\', '/'))
    if path.name.lower().startswith('opencv_videoio_ffmpeg'):
        return True
    if path.parts[:2] == ('torch', 'bin'):
        return (path.name.startswith('test_') and path.suffix in {'', '.exe'}) or path.name in {
            'protoc', 'protoc.exe', 'protoc-3.13.0.0',
            'HashStoreTest', 'FileStoreTest', 'TCPStoreTest',
        }
    return False


def application_modules(root: Path) -> list[str]:
    """Enumerate only our dynamic registry; never import frames while building."""
    return sorted({
        '.'.join(path.relative_to(root).with_suffix('').parts).removesuffix('.__init__')
        for path in (root / 'app').rglob('*.py')
        if '__pycache__' not in path.parts
    })


def runtime_assets(root: Path) -> list[tuple[str, str]]:
    return [
        (str(path), str(path.parent.relative_to(root)))
        for path in sorted((root / 'assets').rglob('*'))
        if path.is_file() and path.suffix not in {'.icns', '.py', '.pyc'}
        and path.name not in INSTALLER_ASSETS
    ]


def runtime_distributions(root: Path, marker_environment: dict | None = None) -> list[str]:
    from packaging.requirements import Requirement

    names = []
    for line in (root / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        if '==' not in line:
            continue
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate(marker_environment):
            names.append(requirement.name)
    return names


def build_inputs(root: Path) -> dict:
    from PyInstaller.utils.hooks import collect_data_files, copy_metadata

    assert_clean_environment()
    datas = runtime_assets(root) + collect_data_files('customtkinter')
    # Preserve licenses and distribution metadata, including PyMatting's runtime lookup.
    for name in runtime_distributions(root):
        datas.extend(copy_metadata(name))
        # Intel wheels also put third-party notices outside their dist-info.
        dist = importlib.metadata.distribution(name)
        for file in dist.files or ():
            if 'licensing' in file.parts and not any('.dist-info' in part for part in file.parts):
                datas.append((str(dist.locate_file(file)), f'licenses/{name}'))
    return {
        'hiddenimports': application_modules(root) + [
            'easyocr.detection', 'easyocr.model.model', 'easyocr.model.vgg_model',
            'pillow_heif', 'cv2', 'rembg', 'onnxruntime.capi._pybind_state',
            'PIL.ImageTk', 'PIL._tkinter_finder',
        ],
        'datas': datas,
        'excludes': EXCLUDES,
        # The upstream EasyOCR hook preserves shared config and limits language data.
        'hooksconfig': {'easyocr': {'lang_codes': OCR_LANGUAGES}},
    }
