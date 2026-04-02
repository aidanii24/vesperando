# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

datas = []
hiddenimports = []
datas += collect_data_files('vesperando_core')
datas += collect_data_files('odfdo')
datas += copy_metadata('odfdo')
hiddenimports += collect_submodules('rich')


a = Analysis(
    ['cli/src/vesperando_cli/__main__.py'],
    pathex=[],
    binaries=[('core/src/vesperando_core/lib/', 'vesperando_core/lib/')],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['cli/src/vesperando_cli/__init__.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vesperando_cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vesperando_cli',
)
