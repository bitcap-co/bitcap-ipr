# -*- mode: python ; coding: utf-8 -*-
import os
import platform

# filepaths
basedir = os.getcwd()
resources = os.path.join(basedir, 'resources')
app = os.path.join(resources, 'app')
icons = os.path.join(app, 'icons')
theme = os.path.join(basedir, 'src/ui/theme')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(app, 'config.json.default'), os.path.join('resources', 'app')), (os.path.join(icons), os.path.join('resources', 'app', 'icons')), (os.path.join(theme, 'theme.qss'), os.path.join('resources', 'app', 'ui'))],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='BitCapIPR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.ico')] if platform.system() == 'Windows' else [os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png')],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BitCapIPR',
)

app = BUNDLE(
    coll,
    name='BitCapIPR.app',
    icon=os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.icns'),
    bundle_identifier=None
)
