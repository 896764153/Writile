# Writile 打包与运行指南

## 支持平台

| 平台 | 打包格式 | 打包工具 | 脚本 |
|------|----------|----------|------|
| Windows | `.exe` + 安装包 | PyInstaller + Inno Setup | `build.spec` + `installer.iss` |
| macOS | `.app` + `.dmg` | PyInstaller + hdiutil | `build_macos.spec` + `build_macos.sh` |
| Linux | 可执行文件 + AppImage | PyInstaller + AppImageTool | `build_linux.spec` + `build_linux.sh` |

---

## 目录

- [环境准备](#环境准备)
- [测试运行](#测试运行)
- [Windows 打包](#windows-打包)
- [macOS 打包](#macos-打包)
- [Linux 打包](#linux-打包)
- [常见问题](#常见问题)
- [文件说明](#文件说明)

---

## 环境准备

### 1. 安装 Python 3.10+

| 平台 | 安装方式 |
|------|----------|
| Windows | 从 [python.org](https://www.python.org/downloads/) 下载，勾选 Add to PATH |
| macOS | `brew install python` 或从 [python.org](https://www.python.org/downloads/) 下载 |
| Linux | `sudo apt install python3 python3-pip` 或对应发行版命令 |

验证安装：

```bash
python3 --version
```

### 2. 安装依赖

```bash
cd MarkdownEditor
pip3 install -r requirements.txt
```

> 如果网络较慢，可使用清华镜像源：
> ```bash
> pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
> ```

### 3. 依赖清单

| 包名 | 用途 |
|------|------|
| PyQt6 | GUI 框架 |
| PyQt6-WebEngine | Markdown 即时渲染（Chromium 内核） |
| Markdown | Markdown 转 HTML |
| Pygments | 代码高亮 |

### 4. Linux 额外系统依赖

Linux 上需要安装 Qt6 运行时库：

```bash
# Ubuntu / Debian
sudo apt install libgl1-mesa-glx libegl1 libxkbcommon0 libdbus-1-3 \
    libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
    libxcb-sync1 libxcb-xfixes0 libxcb-xkb1 libxkbcommon-x11-0 \
    libqt6-webenginecore6 libqt6-webenginewidgets6

# Fedora
sudo dnf install mesa-libGL libxkbcommon dbus-libs qt6-qtwebengine
```

---

## 测试运行

### 直接运行源码（三端通用）

```bash
cd MarkdownEditor
python3 md_editor.py
```

程序启动后即可使用全部功能：

- Markdown 编辑与实时预览（所见即所得）
- 主题切换与可视化主题编辑器
- 快捷键自定义（菜单 → 设置 → 自定义快捷键）
- 导出 HTML / PDF
- 专注模式、打字机模式
- 多标签页编辑

### 用户数据存储路径

| 平台 | 自定义主题路径 | 设置存储 |
|------|----------------|----------|
| Windows | `~/Documents/Writile/themes/` | 注册表 (QSettings) |
| macOS | `~/Documents/Writile/themes/` | `~/Library/Preferences/com.Writile.plist` |
| Linux | `~/.local/share/Writile/themes/` | `~/.config/Writile/` |

---

## Windows 打包

### 1. 安装 PyInstaller

```bash
python -m pip install pyinstaller
```

### 2. 生成图标

```bash
python gen_icon.py
```

### 3. PyInstaller 打包 EXE

```bash
python -m PyInstaller build.spec
```

产物：`dist/Writile.exe`（单文件，所有依赖内嵌）

### 4. Inno Setup 生成安装包

```bash
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

产物：`installer_output/Writile-Setup-1.0.0.exe`

> 详细说明请参考 [Windows 打包常见问题](#常见问题)。

---

## macOS 打包

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

### 2. 一键打包

```bash
chmod +x build_macos.sh
./build_macos.sh
```

### 3. 手动分步打包

```bash
# 生成图标
python3 gen_icon.py

# PyInstaller 打包 .app
python3 -m PyInstaller build_macos.spec --noconfirm

# 创建 DMG 安装包
hdiutil create -volname "Writile" -srcfolder "dist/Writile.app" -ov -format UDZO "dist/Writile-macOS.dmg"
```

### 4. 产物

```
dist/
├── Writile.app           ← macOS 应用（双击运行）
└── Writile-macOS.dmg     ← DMG 安装包
```

### 5. 分发

- **DMG**：将 `Writile-macOS.dmg` 发给用户，双击挂载后拖入 Applications 文件夹
- **App**：直接分发 `Writile.app`（需压缩为 zip）

> **注意**：macOS 上分发的应用可能需要代码签名，否则用户首次打开需在「系统设置 → 隐私与安全性」中允许运行。

---

## Linux 打包

### 1. 安装系统依赖

```bash
sudo apt install libgl1-mesa-glx libegl1 libxkbcommon0 \
    libqt6-webenginecore6 libqt6-webenginewidgets6 wget
```

### 2. 安装 Python 依赖

```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

### 3. 一键打包

```bash
chmod +x build_linux.sh
./build_linux.sh
```

### 4. 手动分步打包

```bash
# 生成图标
python3 gen_icon.py

# PyInstaller 打包
python3 -m PyInstaller build_linux.spec --noconfirm

# 创建 AppImage（需要 appimagetool）
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage dist/Writile dist/Writile-x86_64.AppImage
```

### 5. 产物

```
dist/
├── Writile                    ← 可执行文件（需配合依赖库）
└── Writile-x86_64.AppImage    ← AppImage（推荐分发格式）
```

### 6. 分发

- **AppImage（推荐）**：下载后 `chmod +x Writile-x86_64.AppImage`，双击即可运行
- **可执行文件**：需要目标机器已安装 Qt6 运行时库

---

## 一键打包流程

### Windows

```bash
cd MarkdownEditor
pip install -r requirements.txt
python -m pip install pyinstaller
python gen_icon.py
python -m PyInstaller build.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### macOS

```bash
cd MarkdownEditor
pip3 install -r requirements.txt
pip3 install pyinstaller
chmod +x build_macos.sh
./build_macos.sh
```

### Linux

```bash
cd MarkdownEditor
pip3 install -r requirements.txt
pip3 install pyinstaller
chmod +x build_linux.sh
./build_linux.sh
```

---

## 常见问题

### Windows

#### Q: `pyinstaller` 命令不可用

使用 `python -m PyInstaller` 代替 `pyinstaller`。

#### Q: `iscc` 命令不可用

使用完整路径：`& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

#### Q: Inno Setup 报错找不到中文语言包

已修复，`installer.iss` 使用英文安装界面，程序本身仍为中文。

#### Q: PowerShell 脚本执行被禁止

```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### macOS

#### Q: 运行报错 `ModuleNotFoundError: No module named 'PyQt6'`

```bash
pip3 install PyQt6 PyQt6-WebEngine
```

#### Q: 应用打开后立即闪退

可能是权限问题。右键点击 `Writile.app`，选择「打开」，或在终端运行：

```bash
xattr -cr /path/to/Writile.app
```

#### Q: DMG 打包失败

确保有足够的磁盘空间，并检查 `dist/Writile.app` 是否存在。

#### Q: WebEngine 在 macOS 上黑屏

macOS 上需要确保 PyInstaller 收集了 WebEngine 资源文件。`build_macos.spec` 已配置 hiddenimports。

### Linux

#### Q: 运行报错 `error while loading shared libraries: libQt6WebEngineCore.so`

需要安装 Qt6 WebEngine 运行时库：

```bash
sudo apt install libqt6-webenginecore6 libqt6-webenginewidgets6
```

#### Q: AppImage 无法运行

确保 AppImage 有执行权限：

```bash
chmod +x Writile-x86_64.AppImage
./Writile-x86_64.AppImage
```

如果仍无法运行，尝试 `--appimage-extract-and-run`：

```bash
./Writile-x86_64.AppImage --appimage-extract-and-run
```

#### Q: Fcitx/Sogou 输入法无法使用

设置环境变量：

```bash
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
./Writile
```

### 通用

#### Q: 图标缺失

```bash
python3 gen_icon.py
```

#### Q: 杀毒软件误报

PyInstaller 打包的程序可能被杀毒软件误报。可添加信任或使用代码签名证书。

---

## 文件说明

| 文件 | 用途 | 平台 |
|------|------|------|
| `md_editor.py` | 主程序源码 | 全平台 |
| `gen_icon.py` | 图标生成脚本 | 全平台 |
| `build.spec` | PyInstaller 配置 (Windows) | Windows |
| `build_macos.spec` | PyInstaller 配置 (macOS) | macOS |
| `build_linux.spec` | PyInstaller 配置 (Linux) | Linux |
| `installer.iss` | Inno Setup 安装脚本 | Windows |
| `build_macos.sh` | macOS 打包脚本 | macOS |
| `build_linux.sh` | Linux 打包脚本 | Linux |
| `build.bat` | Windows EXE 打包批处理 | Windows |
| `build_installer.bat` | Windows 安装包打包批处理 | Windows |
| `requirements.txt` | Python 依赖清单 | 全平台 |
| `themes/` | 预设主题 JSON 文件目录 | 全平台 |
| `icon.ico` | 应用图标 (Windows) | Windows |
| `icon.png` | 应用图标 (PNG) | 全平台 |

---

## 项目结构

```
MarkdownEditor/
├── md_editor.py              ← 主程序源码（跨平台）
├── gen_icon.py               ← 图标生成脚本（跨平台）
├── build.spec                ← PyInstaller 配置 (Windows)
├── build_macos.spec          ← PyInstaller 配置 (macOS)
├── build_linux.spec          ← PyInstaller 配置 (Linux)
├── installer.iss             ← Inno Setup 安装脚本 (Windows)
├── build_macos.sh            ← macOS 打包脚本
├── build_linux.sh            ← Linux 打包脚本
├── build.bat                 ← Windows EXE 打包批处理
├── build_installer.bat       ← Windows 安装包打包批处理
├── requirements.txt          ← Python 依赖
├── icon.ico                  ← 应用图标 (Windows)
├── icon.png                  ← 应用图标 (PNG)
├── themes/                   ← 预设主题文件
│   ├── github.json
│   ├── dark.json
│   └── ...
├── dist/                     ← PyInstaller 打包产物
├── installer_output/         ← Windows 安装包产物
├── build/                    ← PyInstaller 中间文件
└── READMD.md                 ← 本文档
```
