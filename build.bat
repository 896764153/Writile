@echo off
REM ============================================================
REM Writile - Build Script
REM Package Python script into a standalone .exe file
REM ============================================================

setlocal enabledelayedexpansion

REM ---- Mirror settings (Tsinghua mirror + SSL bypass) ----
set "PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED=--trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host pypi.org --trusted-host files.pythonhosted.org"

echo ============================================================
echo   Writile - Build .exe
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

echo [1/5] Checking Python environment...
python --version

REM Upgrade pip (with SSL bypass + mirror)
echo.
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip -i %PIP_INDEX% %PIP_TRUSTED%

REM Install dependencies (with SSL bypass + mirror)
echo.
echo [3/5] Installing dependencies...
python -m pip install -r requirements.txt -i %PIP_INDEX% %PIP_TRUSTED%
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo         Try running this command manually:
    echo         pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host files.pythonhosted.org
    pause
    exit /b 1
)

REM Clean old build files
echo.
echo [4/5] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Writile.spec" del /f /q "Writile.spec"

REM Build with PyInstaller
echo.
echo [5/5] Building executable...
python -m PyInstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

REM Verify output
if exist "dist\Writile.exe" (
    echo.
    echo ============================================================
    echo   Build SUCCESS!
    echo   Output: %CD%\dist\Writile.exe
    echo ============================================================
    echo.
    echo You can copy Writile.exe anywhere and run it directly.
    echo.

    set /p open_dir="Open output folder? (y/n): "
    if /i "!open_dir!"=="y" (
        explorer "dist"
    )
) else (
    echo [ERROR] Output file not found.
)

pause
