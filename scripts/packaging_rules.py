"""Shared PyInstaller policy for Windows and Linux (no application imports)."""

from pathlib import Path

EXCLUDES = [
    'pandas', 'pytest', '_pytest', 'pytest_cov', 'coverage', 'tkinterdnd2',
    'rembg.cli', 'rembg.commands', 'torchaudio', 'triton', 'IPython',
    'matplotlib', 'notebook', 'jupyter',
]
INSTALLER_ASSETS = {'installer_icon.ico', 'wizard_image.bmp', 'wizard_small.bmp'}
OCR_LANGUAGES = ['en', 'es']


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


def build_inputs(root: Path) -> dict:
    from PyInstaller.utils.hooks import collect_data_files, copy_metadata

    datas = runtime_assets(root) + collect_data_files('customtkinter')
    # Preserve licenses and distribution metadata, including PyMatting's runtime lookup.
    for line in (root / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        if '==' in line:
            datas.extend(copy_metadata(line.split('==')[0]))
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
