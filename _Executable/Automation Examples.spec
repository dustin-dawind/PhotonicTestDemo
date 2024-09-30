# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\startup.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\resources\\', 'resources'),
           # ('..\\resources\\testing_definitions', '..\\resources\\testing_definitions'),
           # ('..\\resources\\logo.jpg', '..\\resources'),
           # ('..\\resources\\logo.ico', '..\\resources'),
           ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    '..\\resources\\splash_screen.jpg',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(10, 230),
    text_size=12,
    text_color='white',
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='Automation Examples',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='..\\resources\\logo.ico',
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    splash.binaries,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Automation Examples',
)
