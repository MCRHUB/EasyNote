# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置（Windows）
打包命令：python -m PyInstaller build.spec --noconfirm
产物：dist/NoteBook.exe
"""
import os
import sys

block_cipher = None
BASE = os.path.abspath('.')

datas = [
    (os.path.join(BASE, 'static'), 'static'),
    (os.path.join(BASE, 'templates'), 'templates'),
]

hiddenimports = [
    'flask',
    'flask.templating',
    'jinja2',
    'jinja2.ext',
    'webview',
    'webview.platforms',
    'webview.platforms.winforms',
]

a = Analysis(
    ['main.py'],
    pathex=[BASE],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NoteBook',
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
    icon=os.path.join(BASE, 'icon.ico'),
)