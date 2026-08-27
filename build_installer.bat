@echo off
REM ============================================================
REM Writile - Build Installer Script
REM Requires: Inno Setup (https://jrsoftware.org/isdl.php)
REM ============================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

set "LOG=%~dp0build_installer.log"
del /f /q "%LOG%" >nul 2>&1

goto :MAIN

:ECHO_LOG
setlocal
set "LINE=%*"
if defined LINE (
    >>"%LOG%" echo %LINE%
    echo %LINE%
) else (
    >>"%LOG%" echo.
    echo.
)
endlocal
exit /b 0

:LAST_LINES
setlocal
set "N=%~1"
set "LOGFILE=%~2"
if not defined LOGFILE set "LOGFILE=%LOG%"
if not exist "%LOGFILE%" exit /b 0
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; Get-Content '%LOGFILE%' -Tail %N% 2>$null"
endlocal
exit /b 0

REM ============================================================
:MAIN
REM ============================================================

call :ECHO_LOG ============================================================
call :ECHO_LOG   Writile - Build Installer
call :ECHO_LOG ============================================================
call :ECHO_LOG
call :ECHO_LOG   Log: %LOG%
call :ECHO_LOG

REM Step 1: Ensure icon (icon.png / icon.ico 已存在则跳过生成)
call :ECHO_LOG [Step 1/4] Checking icon...
if exist "icon.png" if exist "icon.ico" (
    call :ECHO_LOG           icon.png / icon.ico already exist, skipping generation.
    goto :ICON_DONE
)
set "PYCMD="
py --version >nul 2>&1 && set "PYCMD=py"
if not defined PYCMD python --version >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD python3 --version >nul 2>&1 && set "PYCMD=python3"
if not defined PYCMD (
    call :ECHO_LOG [ERROR] Python not found. Please install Python 3.9+ and add to PATH.
    exit /b 1
)
if not exist "gen_icon.py" (
    call :ECHO_LOG [ERROR] icon.png / icon.ico missing and gen_icon.py not found.
    exit /b 1
)
"%PYCMD%" gen_icon.py >>"%LOG%" 2>&1
if errorlevel 1 (
    call :ECHO_LOG [ERROR] Failed to generate icon.
    call :LAST_LINES 20
    exit /b 1
)
:ICON_DONE
call :ECHO_LOG

REM Step 2: Build exe (delegates to build.bat with its own build.log)
call :ECHO_LOG [Step 2/4] Building Writile.exe
call :ECHO_LOG ------------------------------------------------------------
call build.bat >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
REM Echo build.bat summary lines (last 10) to console so user sees progress
call :LAST_LINES 10 "%~dp0build.log"
if "%RC%" NEQ "0" (
    call :ECHO_LOG
    call :ECHO_LOG [ERROR] Failed to build Writile.exe
    call :ECHO_LOG
    call :ECHO_LOG   build.log       : %~dp0build.log
    call :ECHO_LOG   build_installer : %LOG%
    exit /b 1
)
call :ECHO_LOG

REM Step 3: Check Inno Setup
call :ECHO_LOG [Step 3/4] Checking Inno Setup...
set "ISCC="

REM Priority 1: env var override
if defined INNO_SETUP_PATH if exist "%INNO_SETUP_PATH%\ISCC.exe" set "ISCC=%INNO_SETUP_PATH%\ISCC.exe"
if defined INNO_SETUP_PATH if exist "%INNO_SETUP_PATH%" for %%I in ("%INNO_SETUP_PATH%") do if /i "%%~nxI"=="ISCC.exe" set "ISCC=%INNO_SETUP_PATH%"

REM Priority 2: first arg
if not defined ISCC if not "%~1"=="" if exist "%~1\ISCC.exe" set "ISCC=%~1\ISCC.exe"
if not defined ISCC if not "%~1"=="" if exist "%~1" for %%I in ("%~1") do if /i "%%~nxI"=="ISCC.exe" set "ISCC=%~1"

REM Priority 3: common install paths (one line each to avoid (x86) parenthesis issues)
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 5\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 5\ISCC.exe"
if not defined ISCC if exist "D:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=D:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "D:\Program Files\Inno Setup 5\ISCC.exe" set "ISCC=D:\Program Files\Inno Setup 5\ISCC.exe"
if not defined ISCC if exist "E:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=E:\Program Files\Inno Setup 6\ISCC.exe"

REM Priority 4: (x86) paths - use call to subroutine to avoid parenthesis parsing issues
if not defined ISCC call :FIND_ISCC_X86

REM Priority 5: per-user install paths
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Inno Setup 6\ISCC.exe"

REM Priority 6: PATH / chocolatey / scoop shims
if not defined ISCC for /f "delims=" %%Q in ('where ISCC 2^>nul') do if exist "%%Q" set "ISCC=%%Q"
if not defined ISCC if exist "%ChocolateyInstall%\bin\ISCC.exe" set "ISCC=%ChocolateyInstall%\bin\ISCC.exe"
if not defined ISCC if exist "%USERPROFILE%\scoop\shims\ISCC.exe" set "ISCC=%USERPROFILE%\scoop\shims\ISCC.exe"

REM Priority 7: registry lookup
if not defined ISCC call :FIND_ISCC_REG

goto :ISCC_DONE

REM --- Subroutine: check (x86) paths ---
:FIND_ISCC_X86
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if exist "D:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=D:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "D:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "ISCC=D:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if exist "E:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=E:\Program Files (x86)\Inno Setup 6\ISCC.exe"
exit /b 0

REM --- Subroutine: check registry uninstall entries ---
:FIND_ISCC_REG
for %%R in (
    "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
    "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
    "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
    "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1"
    "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1"
    "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1"
) do (
    for /f "tokens=2*" %%A in ('reg query %%R /v "InstallLocation" 2^>nul ^| findstr /i "InstallLocation"') do (
        if exist "%%B\ISCC.exe" set "ISCC=%%B\ISCC.exe"
    )
)
exit /b 0

:ISCC_DONE

if "%ISCC%"=="" (
    call :ECHO_LOG [WARN] Inno Setup not found - skipping installer package.
    call :ECHO_LOG
    call :ECHO_LOG   Standalone EXE is ready: dist\Writile.exe
    call :ECHO_LOG
    call :ECHO_LOG   To build the installer ^(Writile-Setup-^<version^>.exe^), install Inno Setup 6:
    call :ECHO_LOG     Option 1 - winget, recommended:
    call :ECHO_LOG       winget install JRSoftware.InnoSetup
    call :ECHO_LOG     Option 2 - chocolatey:
    call :ECHO_LOG       choco install innosetup
    call :ECHO_LOG     Option 3 - manual download:
    call :ECHO_LOG       https://jrsoftware.org/isdl.php
    call :ECHO_LOG
    call :ECHO_LOG   After installing, re-run build_installer.bat to produce the Setup package.
    call :ECHO_LOG
    exit /b 0
)

call :ECHO_LOG Found Inno Setup: "%ISCC%"
call :ECHO_LOG

REM Step 4: Build installer
call :ECHO_LOG [Step 4/4] Building installer...
"%ISCC%" installer.iss >>"%LOG%" 2>&1
set "ISCC_RC=%ERRORLEVEL%"
if "%ISCC_RC%" NEQ "0" (
    call :ECHO_LOG [ERROR] Inno Setup returned exit code %ISCC_RC%.
    call :LAST_LINES 30
    exit /b 1
)

call :ECHO_LOG
call :ECHO_LOG ============================================================
call :ECHO_LOG   Build SUCCESS!
call :ECHO_LOG ============================================================
REM 自动识别最新生成的安装包文件名（版本号在 installer.iss 中，不在此硬编码）
set "SETUP_EXE="
for %%F in (installer_output\Writile-Setup-*.exe) do set "SETUP_EXE=%%~nxF"

call :ECHO_LOG Output files:
call :ECHO_LOG   Standalone:  dist\Writile.exe
if defined SETUP_EXE (
    call :ECHO_LOG   Installer:   installer_output\%SETUP_EXE%
    call :ECHO_LOG
    call :ECHO_LOG Installer is ready!
) else (
    call :ECHO_LOG   Installer:   ^(not found^)
    call :ECHO_LOG
    call :ECHO_LOG [WARN] Installer file not found under installer_output\
)
