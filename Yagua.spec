# -*- mode: python ; coding: utf-8 -*-

import os
import importlib.metadata as importlib_metadata
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

project_root = os.getcwd()

hiddenimports = []
hiddenimports.append('app.ui.frames')
hiddenimports += collect_submodules('app.ui.frames')
hiddenimports += collect_submodules('app.modules')
hiddenimports += collect_submodules('app.utils')
hiddenimports += collect_submodules('app.translations')
# OCR / HEIC / Vectorizar
hiddenimports += collect_submodules('easyocr')
hiddenimports += [
    'easyocr',
    'pillow_heif',
    'vtracer',
    'cv2',
]
# Forzar inclusion de frames y subcomponentes que fallan en runtime
hiddenimports += [
    'app.ui.frames.remove_bg',
    'app.ui.frames.remove_bg.frame',
    'app.ui.frames.remove_bg.services',
    'app.ui.frames.remove_bg.state',
    'app.ui.frames.rename',
    'app.ui.frames.rename.frame',
    'app.ui.frames.rename.services',
    'app.ui.frames.rename.state',
    'app.ui.frames.lqip',
    'app.ui.frames.lqip.frame',
    'app.ui.frames.lqip.services',
    'app.ui.frames.lqip.state',
    'app.ui.frames.image_transform',
    'app.ui.frames.image_transform.frame',
    'app.ui.frames.image_transform.services',
    'app.ui.frames.image_transform.state',
    'app.ui.frames.vectorizar',
    'app.ui.frames.vectorizar.frame',
    'app.ui.frames.vectorizar.services',
    'app.ui.frames.vectorizar.state',
    'app.ui.frames.watermark',
    'app.ui.frames.watermark.frame',
    'app.ui.frames.watermark.services',
    'app.ui.frames.watermark.state',
    'app.ui.frames.ocr',
    'app.ui.frames.ocr.frame',
    'app.ui.frames.ocr.services',
    'app.ui.frames.ocr.state',
]
# Dependencias con metadata requerida por rembg
hiddenimports += collect_submodules('pymatting')
# Dependencias usadas por remove_bg (imports dinamicos)
hiddenimports += collect_submodules('rembg')
hiddenimports += [
    'rembg',
    'onnxruntime',
    'onnxruntime.capi._pybind_state',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
]

# Data files (assets + translations + user settings)
datas = []
datas += [('assets', 'assets')]
datas += collect_data_files('customtkinter')
datas += collect_data_files('app.translations')
datas += collect_data_files('easyocr')

# Agregar metadata de pymatting para evitar "No package metadata was found"
try:
    dist = importlib_metadata.distribution('pymatting')
    if dist is not None and dist._path:
        datas.append((str(dist._path), dist._path.name))
except Exception:
    pass


a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Yagua',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Yagua',
)
