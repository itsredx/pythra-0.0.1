# v_list.spec
# -*- mode: python ; coding: utf-8 -*-

added_files = [
    ('web', 'web'),
    ('assets', 'assets'),
    ('config.yaml', '.'),
]

a = Analysis(
    ['v_list.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PySide6.QtSvg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyVirtualListApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
