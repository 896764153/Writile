# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件 (Linux)
用于将 Writile 打包为可执行文件 / AppImage
"""

import sys
import os

block_cipher = None

# 收集所有主题文件
datas = [('icon.png', '.')]
themes_dir = os.path.join(SPECPATH, 'themes')
if os.path.isdir(themes_dir):
    for fname in os.listdir(themes_dir):
        if fname.endswith('.json'):
            datas.append((os.path.join(themes_dir, fname), 'themes'))

a = Analysis(
    ['md_editor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebChannel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'argparse',
    ],
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
    name='Writile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png',
)
