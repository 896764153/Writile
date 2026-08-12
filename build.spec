# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件 (Windows)
用于将 Writile 打包为单个 .exe 文件
macOS 请使用 build_macos.spec，Linux 请使用 build_linux.spec
"""

import sys
import os

block_cipher = None

# 收集所有主题文件
datas = [('icon.ico', '.'), ('icon.png', '.')]
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
        # 确保这些模块被打包
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
        # 排除不需要的模块以减小体积
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
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'msvcp140.dll',
        'python3.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6WebEngineCore.dll',
        'Qt6WebEngineWidgets.dll',
        'Qt6Network.dll',
        'Qt6OpenGL.dll',
        'Qt6PrintSupport.dll',
        'Qt6Qml.dll',
        'Qt6QmlModels.dll',
        'Qt6Quick.dll',
        'Qt6QuickWidgets.dll',
        'Qt6Svg.dll',
        'Qt6WebChannel.dll',
        'Qt6Positioning.dll',
        'Qt6Designer.dll',
        'Qt6Help.dll',
        'Qt6Multimedia.dll',
        'Qt6MultimediaWidgets.dll',
        'Qt6Sql.dll',
        'Qt6Test.dll',
        'Qt6Xml.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 应用图标
)
