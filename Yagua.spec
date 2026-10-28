# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import runpy

project_root = Path(SPECPATH)
# La política compartida concentra imports dinámicos y recursos runtime.
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
# Excluir solo herramientas de desarrollo identificadas y el plugin de video de Windows.
# Conservar completos los módulos de Torch/SciPy y sus DLL/SO de runtime.
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
