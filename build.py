# -*- coding: utf-8 -*-
"""
Markdown 编辑器 - 构建脚本
功能：使用 PyInstaller 将程序打包为单个 .exe 文件
使用方法：python build.py
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 9):
        print("[错误] 需要 Python 3.9 或更高版本")
        print(f"当前版本: {platform.python_version()}")
        sys.exit(1)
    print(f"[OK] Python 版本: {platform.python_version()}")


def install_dependencies():
    """安装项目依赖"""
    print("\n[步骤 1] 安装项目依赖...")
    requirements = Path("requirements.txt")
    if not requirements.exists():
        print("[错误] 未找到 requirements.txt")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("[错误] 依赖安装失败")
        sys.exit(1)
    print("[OK] 依赖安装完成")


def clean_old_build():
    """清理旧的构建文件"""
    print("\n[步骤 2] 清理旧构建文件...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for d in dirs_to_clean:
        if Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)
            print(f"  已删除: {d}")

    spec_file = Path("MarkdownEditor.spec")
    if spec_file.exists():
        spec_file.unlink()
        print(f"  已删除: MarkdownEditor.spec")
    print("[OK] 清理完成")


def build_executable():
    """使用 PyInstaller 打包"""
    print("\n[步骤 3] 开始打包...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "build.spec",
        "--clean",
        "--noconfirm",
        "--log-level", "WARN",
    ]

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("[错误] 打包失败")
        sys.exit(1)
    print("[OK] 打包完成")


def verify_output():
    """验证输出文件"""
    print("\n[步骤 4] 验证输出...")
    exe_path = Path("dist") / "MarkdownEditor.exe"
    if not exe_path.exists():
        print(f"[错误] 未找到输出文件: {exe_path}")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"[OK] 输出文件: {exe_path.absolute()}")
    print(f"     文件大小: {size_mb:.2f} MB")
    return exe_path


def create_portable_package(exe_path):
    """创建便携版压缩包"""
    print("\n[步骤 5] 创建便携版压缩包...")

    try:
        import zipfile
    except ImportError:
        print("[跳过] 无法创建压缩包（缺少 zipfile 模块）")
        return

    zip_path = Path("dist") / "MarkdownEditor-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(exe_path, exe_path.name)
        print(f"[OK] 便携版: {zip_path.absolute()}")


def main():
    print("=" * 60)
    print("  Markdown 编辑器 - 构建工具")
    print("=" * 60)

    # 切换到脚本目录
    os.chdir(Path(__file__).parent)

    check_python_version()
    install_dependencies()
    clean_old_build()
    build_executable()
    exe_path = verify_output()
    create_portable_package(exe_path)

    print("\n" + "=" * 60)
    print("  构建完成！")
    print("=" * 60)
    print(f"\n可执行文件位置: {exe_path.absolute()}")
    print(f"便携版压缩包:   {Path('dist/MarkdownEditor-portable.zip').absolute()}")
    print("\n提示: 可以直接运行 .exe 文件，或将其复制到任意位置使用。")
    print("\n按 Enter 退出...")
    input()


if __name__ == "__main__":
    main()
