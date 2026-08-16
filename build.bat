@echo off
REM ============================================================
REM Writile - Build Script
REM Package Python script into a standalone .exe file
REM ============================================================

setlocal enabledelayedexpansion

REM ---- Mirror settings (Tsinghua mirror + SSL bypass) ----
set "PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED=--trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host pypi.org --trusted-host files.pythonhosted.org"

cd /d "%~dp0"

REM Log file: full verbose output written here (console shows summary + tail on error)
set "LOG=%~dp0build.log"
del /f /q "%LOG%" >nul 2>&1

REM ============================================================
REM Helper subroutines
REM ============================================================
goto :MAIN

:ECHO_LOG
REM Echo args to both console AND log file.
REM If no args given, just emit blank line.
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
REM Print last N=%1 lines from LOG to console.
setlocal
set "N=%~1"
if not exist "%LOG%" exit /b 0
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; Get-Content '%LOG%' -Tail %N% 2>$null"
endlocal
exit /b 0

REM ============================================================
:MAIN
REM ============================================================

call :ECHO_LOG ============================================================
call :ECHO_LOG   Writile - Build .exe
call :ECHO_LOG ============================================================
call :ECHO_LOG
call :ECHO_LOG   Log: %LOG%
call :ECHO_LOG

REM Detect Python: try py launcher, python, python3, then scan common paths
set "PYCMD="
py --version >nul 2>&1 && set "PYCMD=py"
if not defined PYCMD python --version >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD python3 --version >nul 2>&1 && set "PYCMD=python3"

if not defined PYCMD (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
        "C:\Python39\python.exe"
        "C:\Program Files\Python313\python.exe"
        "C:\Program Files\Python312\python.exe"
        "C:\Program Files\Python311\python.exe"
        "C:\Program Files\Python310\python.exe"
        "C:\Program Files (x86)\Python313\python.exe"
        "C:\Program Files (x86)\Python312\python.exe"
        "C:\Program Files (x86)\Python311\python.exe"
        "C:\Program Files (x86)\Python310\python.exe"
    ) do (
        if exist %%P set "PYCMD=%%~P"
    )
)

if not defined PYCMD (
    call :ECHO_LOG [ERROR] Python not found.
    call :ECHO_LOG         Tried: py, python, python3, and common install paths.
    call :ECHO_LOG
    call :ECHO_LOG         Please install Python 3.9+ from https://www.python.org/downloads/
    call :ECHO_LOG         and check "Add Python to PATH" during installation.
    exit /b 1
)

call :ECHO_LOG [1/5] Checking Python environment...
"%PYCMD%" --version >>"%LOG%" 2>&1
for /f "delims=" %%v in ('"%PYCMD%" --version 2^>^&1') do set "VER=%%v"
call :ECHO_LOG       %VER%

REM Upgrade pip (with SSL bypass + mirror)
call :ECHO_LOG
call :ECHO_LOG [2/5] Upgrading pip...
"%PYCMD%" -m pip install --upgrade pip -i %PIP_INDEX% %PIP_TRUSTED% >>"%LOG%" 2>&1

REM Install dependencies (with SSL bypass + mirror)
call :ECHO_LOG
call :ECHO_LOG [3/5] Installing dependencies...
"%PYCMD%" -m pip install -r requirements.txt -i %PIP_INDEX% %PIP_TRUSTED% >>"%LOG%" 2>&1
if errorlevel 1 (
    call :ECHO_LOG
    call :ECHO_LOG [ERROR] Step 3 failed: could not install dependencies.
    call :ECHO_LOG
    call :LAST_LINES 30
    call :ECHO_LOG
    call :ECHO_LOG Full log: %LOG%
    exit /b 1
)

REM Clean old build files
call :ECHO_LOG
call :ECHO_LOG [4/5] Cleaning old build files...
taskkill /F /IM Writile.exe >>"%LOG%" 2>&1
timeout /t 1 /nobreak >nul

if exist "build" (
    rmdir /s /q "build" >>"%LOG%" 2>&1
    if exist "build" call :ECHO_LOG       [WARN] build dir still in use, continuing anyway.
)

set "DIST_LOCKED=0"
if exist "dist" (
    rmdir /s /q "dist" >>"%LOG%" 2>&1
    if exist "dist" (
        if exist "dist_old" rmdir /s /q "dist_old" >>"%LOG%" 2>&1
        move /y "dist" "dist_old" >>"%LOG%" 2>&1
        if exist "dist_old" rmdir /s /q "dist_old" >>"%LOG%" 2>&1
    )
    if exist "dist\Writile.exe" set "DIST_LOCKED=1"
)
if exist "Writile.spec" del /f /q "Writile.spec" >>"%LOG%" 2>&1

if "%DIST_LOCKED%"=="1" (
    call :ECHO_LOG
    call :ECHO_LOG [ERROR] dist\Writile.exe is still locked.
    call :ECHO_LOG
    call :ECHO_LOG Possible causes:
    call :ECHO_LOG   - Writile.exe is still running
    call :ECHO_LOG   - An Explorer window is open on the dist folder
    call :ECHO_LOG   - Antivirus is scanning Writile.exe
    call :ECHO_LOG
    call :ECHO_LOG Action: Close Explorer windows showing "%CD%\dist" then retry.
    exit /b 1
)

REM Build with PyInstaller
call :ECHO_LOG
call :ECHO_LOG [5/5] Building executable... (This may take a few minutes)
"%PYCMD%" -m PyInstaller build.spec --clean --noconfirm >>"%LOG%" 2>&1
set "BUILD_RC=%ERRORLEVEL%"

if "%BUILD_RC%" NEQ "0" (
    call :ECHO_LOG
    call :ECHO_LOG [ERROR] Step 5 failed: PyInstaller returned exit code %BUILD_RC%.
    call :ECHO_LOG
    call :ECHO_LOG -------- Last 50 lines of build.log --------
    call :LAST_LINES 50
    call :ECHO_LOG ------------------------------------------------------------
    call :ECHO_LOG
    call :ECHO_LOG Full log: %LOG%
    exit /b 1
)

REM Verify output
if exist "dist\Writile.exe" (
    call :ECHO_LOG
    call :ECHO_LOG ============================================================
    call :ECHO_LOG   Build SUCCESS!
    call :ECHO_LOG   Output: %CD%\dist\Writile.exe
    call :ECHO_LOG   Log  : %LOG%
    call :ECHO_LOG ============================================================
    call :ECHO_LOG
) else (
    call :ECHO_LOG [ERROR] Build finished but dist\Writile.exe was not produced.
    call :LAST_LINES 30
    exit /b 1
)
