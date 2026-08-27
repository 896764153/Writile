@echo off
rem Writile 启动脚本
rem 原因：本机 PATH 中的 python 指向 Windows Store 占位程序（WindowsApps\python.exe），
rem 它不是真正的解释器，运行任何脚本都会静默退出（表现为"闪退"）。
rem 必须使用 py 启动器或完整路径调用真正的 Python。

where py >nul 2>nul
if %errorlevel%==0 (
    py md_editor.py %*
) else (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" md_editor.py %*
)