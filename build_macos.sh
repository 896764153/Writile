#!/bin/bash
# Writile macOS 打包脚本
# 在 macOS 上运行此脚本生成 .app 应用和 .dmg 安装包

set -e

echo "========================================="
echo "  Writile macOS 打包脚本"
echo "========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

# 安装依赖
echo ""
echo "[1/4] 安装 Python 依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 生成图标
echo ""
echo "[2/4] 生成图标..."
python3 gen_icon.py

# PyInstaller 打包
echo ""
echo "[3/4] PyInstaller 打包..."
python3 -m PyInstaller build.spec --noconfirm

# 创建 .dmg 安装包
echo ""
echo "[4/4] 创建 DMG 安装包..."
APP_DIR="dist/Writile.app"
DMG_NAME="dist/Writile-macOS.dmg"

if [ -d "$APP_DIR" ]; then
    # 删除旧的 DMG
    rm -f "$DMG_NAME"
    # 创建 DMG
    hdiutil create -volname "Writile" -srcfolder "$APP_DIR" -ov -format UDZO "$DMG_NAME"
    echo ""
    echo "========================================="
    echo "  打包完成!"
    echo "========================================="
    echo ""
    echo "  App:  dist/Writile.app"
    echo "  DMG:  dist/Writile-macOS.dmg"
    echo ""
else
    echo "错误: 未找到 dist/Writile.app"
    echo "请检查 PyInstaller 打包是否成功"
    exit 1
fi
