# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\MCGS\\MCGS Web\\main.py'],
    pathex=[],
    binaries=[('E:\\MCGS\\MCGS Web\\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins\\platforms', 'PyQt5/Qt5/plugins/platforms'), ('E:\\MCGS\\MCGS Web\\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins\\styles', 'PyQt5/Qt5/plugins/styles')],
    datas=[('E:\\MCGS\\MCGS Web\\assets\\icons', 'assets/icons'), ('E:\\MCGS\\MCGS Web\\ui', 'ui'), ('E:\\MCGS\\MCGS Web\\utils', 'utils'), ('E:\\MCGS\\MCGS Web\\database', 'database'), ('E:\\MCGS\\MCGS Web\\core', 'core')],
    hiddenimports=['PyQt5', 'sqlite3', 'requests', 'pandas', 'xlsxwriter', 'logging', 'datetime', 'json', 'sys', 'os', 'threading', 'queue'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('v', None, 'OPTION')],
    exclude_binaries=True,
    name='MCGS Web',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\MCGS\\MCGS Web\\assets\\icons\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MCGS Web',
)
