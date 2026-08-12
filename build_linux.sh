#!/bin/bash
# Writile Linux 打包脚本
# 在 Linux 上运行此脚本生成 AppImage

set -e

echo "========================================="
echo "  Writile Linux 打包脚本"
echo "========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

# 安装依赖
echo ""
echo "[1/5] 安装 Python 依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 生成图标
echo ""
echo "[2/5] 生成图标..."
python3 gen_icon.py

# PyInstaller 打包
echo ""
echo "[3/5] PyInstaller 打包..."
python3 -m PyInstaller build.spec --noconfirm

APP_NAME="Writile"
APP_DIR="dist/${APP_NAME}"
APPIMAGE_NAME="dist/Writile-x86_64.AppImage"

# 创建 .desktop 文件
echo ""
echo "[4/5] 创建 .desktop 文件..."
mkdir -p "${APP_DIR}"
cat > "${APP_DIR}/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Name=Writile
Comment=Typora-style Markdown editor
Exec=Writile %f
Icon=writile
Type=Application
Categories=TextEditor;Office;
MimeType=text/markdown;text/x-markdown;
Terminal=false
StartupWMClass=Writile
EOF

# 复制图标
if [ -f "icon.png" ]; then
    mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"
    cp icon.png "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/writile.png"
fi

# 尝试创建 AppImage
echo ""
echo "[5/5] 创建 AppImage..."

# 下载 appimagetool
APPIMAGETOOL="appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "下载 appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

if [ -f "$APPIMAGETOOL" ]; then
    ARCH=x86_64 ./"$APPIMAGETOOL" "$APP_DIR" "$APPIMAGE_NAME" --appimage-extract-and-run 2>/dev/null || \
    ARCH=x86_64 ./"$APPIMAGETOOL" "$APP_DIR" "$APPIMAGE_NAME"
    echo ""
    echo "========================================="
    echo "  打包完成!"
    echo "========================================="
    echo ""
    echo "  可执行文件: dist/Writile"
    echo "  AppImage:   ${APPIMAGE_NAME}"
    echo ""
else
    echo ""
    echo "========================================="
    echo "  打包完成 (AppImage 创建失败)"
    echo "========================================="
    echo ""
    echo "  可执行文件: dist/Writile"
    echo ""
    echo "  手动创建 AppImage:"
    echo "    wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "    chmod +x appimagetool-x86_64.AppImage"
    echo "    ./appimagetool-x86_64.AppImage dist/Writile Writile-x86_64.AppImage"
    echo ""
fi
