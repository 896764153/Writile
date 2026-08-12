@echo off
REM ============================================================
REM Writile - Build Installer Script
REM Requires: Inno Setup (https://jrsoftware.org/isdl.php)
REM ============================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   Writile - Build Installer
echo ============================================================
echo.

REM Step 1: Generate icon
echo [Step 1/4] Generating icon...
python gen_icon.py
if errorlevel 1 (
    echo [ERROR] Failed to generate icon.
    pause
    exit /b 1
)
echo.

REM Step 2: Build exe
echo [Step 2/4] Building Writile.exe
echo ------------------------------------------------------------
call build.bat
if errorlevel 1 (
    echo [ERROR] Failed to build Writile.exe
    pause
    exit /b 1
)
echo.

REM Step 3: Check Inno Setup
echo [Step 3/4] Checking Inno Setup...
set "ISCC="
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    "C:\Program Files\Inno Setup 5\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%~P"
)

if "%ISCC%"=="" (
    echo [ERROR] Inno Setup not found!
    echo         Please download and install Inno Setup 6 from:
    echo         https://jrsoftware.org/isdl.php
    echo.
    echo You can directly use: dist\Writile.exe
    pause
    exit /b 1
)

echo Found Inno Setup: %ISCC%
echo.

REM Step 4: Build installer
echo [Step 4/4] Building installer...
"%ISCC%" installer.iss
if errorlevel 1 (
    echo [ERROR] Failed to build installer.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build SUCCESS!
echo ============================================================
echo Output files:
echo   Standalone:  dist\Writile.exe
echo   Installer:   installer_output\Writile-Setup-1.0.0.exe
echo.

if exist "installer_output\Writile-Setup-1.0.0.exe" (
    echo Installer is ready!
    set /p open_dir="Open output folder? (y/n): "
    if /i "!open_dir!"=="y" (
        explorer "installer_output"
    )
) else (
    echo [ERROR] Installer file not found.
)

pause
