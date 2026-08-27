# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件 (macOS)
用于将 Writile 打包为 .app 应用
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

# lib/ 运行时资源（highlight.min.js 代码高亮等），缺失会导致打包版高亮失效
lib_dir = os.path.join(SPECPATH, 'lib')
if os.path.isdir(lib_dir):
    datas.append((os.path.join(lib_dir, '*'), 'lib'))

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
)

# macOS .app 目录结构
app = BUNDLE(
    exe,
    name='Writile.app',
    icon='icon.png',
    bundle_identifier='com.writile.app',
    info_plist={
        'CFBundleDisplayName': 'Writile',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
        'NSHumanReadableCopyright': 'Copyright © 2026 Writile',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Markdown Document',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['net.daringfireball.markdown'],
                'CFBundleTypeIconFile': 'icon.png',
            }
        ],
    },
)
