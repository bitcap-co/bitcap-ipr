# -*- mode: python ; coding: utf-8 -*-
import os
import platform

# filepaths
basedir = os.getcwd()
resources = os.path.join(basedir, 'src/resources')
icons = os.path.join(resources, 'icons/app')
scalable = os.path.join(resources, 'scalable')
settings = os.path.join(basedir, 'src/config.json')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(icons), os.path.join('resources', 'icons', 'app')), (os.path.join(scalable, 'BitCapIPRCenterLogo.svg'), os.path.join('resources', 'scalable')), (settings, '.')],
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

# app = BUNDLE(
#    coll,
#    name='BitCapIPR.app',
#    icon=os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.icns'),
#    bundle_identifier=None
#)
