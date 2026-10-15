# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import runpy

project_root = Path(SPECPATH)
rules = runpy.run_path(str(project_root / 'scripts' / 'packaging_rules.py'))
inputs = rules['build_inputs'](project_root)
block_cipher = None

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=inputs['datas'],
    hiddenimports=inputs['hiddenimports'],
    hookspath=[],
    hooksconfig=inputs['hooksconfig'],
    runtime_hooks=[],
    excludes=inputs['excludes'],
    cipher=block_cipher,
    noarchive=False,
)
# Headless OpenCV still ships a video-only FFmpeg plugin on Windows. Yagua
# uses Pillow codecs for files and cv2 only for arrays/OCR, never VideoCapture.
a.binaries = [entry for entry in a.binaries
              if not Path(entry[0]).name.lower().startswith('opencv_videoio_ffmpeg')]
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
    icon='assets/icon.png',
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
