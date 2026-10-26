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
    runtime_hooks=[str(project_root / 'scripts' / 'pyinstaller' / 'disable_numba_coverage.py')],
    excludes=inputs['excludes'],
    cipher=block_cipher,
    noarchive=False,
)
# Filter only proven developer programs and the Windows video plugin.
# Keep all runtime Torch/SciPy modules and DLL/SO dependencies intact.
for collection in (a.datas, a.binaries):
    collection[:] = [entry for entry in collection
                     if not rules['omit_packaged_file'](entry[0])]
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
