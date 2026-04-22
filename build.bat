@echo off
REM ============================================================
REM  Build script: compiles auto_warm_up.py into a standalone .exe.
REM
REM  PRIMARY builder: Nuitka (Python -> C -> native PE binary).
REM    -> Dramatically fewer antivirus false positives than
REM       PyInstaller. Recommended for all Windows builds.
REM
REM  FALLBACK builder: PyInstaller (used only if --pyinstaller
REM    is passed explicitly or Nuitka is unavailable).
REM
REM  Usage:
REM    build.bat               (Nuitka, recommended)
REM    build.bat --pyinstaller (legacy PyInstaller path)
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo === Auto Warm-Up Build Script ===
echo.

REM Parse argument to pick the builder (default = Nuitka)
set BUILDER=nuitka
if /I "%~1"=="--pyinstaller" set BUILDER=pyinstaller

REM Step 1: Install dependencies (user-level, no admin needed)
echo [1/4] Installing dependencies...
pip install --user -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

REM Step 2: Generate the multi-size .ico icon file using Pillow
echo [2/4] Generating application icon...
python generate_icon.py app.ico
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Icon generation failed.
    pause
    exit /b 1
)

REM Step 3: Generate PE version info from the VERSION file
echo [3/4] Generating version info...
python generate_version_info.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Version info generation failed.
    pause
    exit /b 1
)

REM Step 4: Build the .exe with the selected builder
if /I "%BUILDER%"=="nuitka" goto BUILD_NUITKA
goto BUILD_PYINSTALLER


:BUILD_NUITKA
echo [4/4] Building .exe with Nuitka (low AV false-positive path)...
echo        Note: first run downloads MinGW-w64 automatically (~100 MB).
echo.

REM Read version string from VERSION file for PE metadata fields
set /p APP_VERSION=<VERSION

REM Nuitka compiles Python source to C, then to a real native PE executable.
REM Unlike PyInstaller, there is no shared bootloader stub for AV engines
REM to fingerprint, so heuristic false positives are drastically reduced.
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app.ico ^
    --company-name="Aditya Bhalsod" ^
    --product-name="Auto Warm-Up" ^
    --file-version=%APP_VERSION% ^
    --product-version=%APP_VERSION% ^
    --file-description="Keep-alive utility that prevents Windows screen lock" ^
    --copyright="Copyright (c) 2024-2026 Aditya Bhalsod. MIT License." ^
    --assume-yes-for-downloads ^
    --output-dir=dist ^
    --output-filename=AutoWarmUp.exe ^
    --remove-output ^
    auto_warm_up.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Nuitka build failed. You can retry with: build.bat --pyinstaller
    pause
    exit /b 1
)
goto DONE


:BUILD_PYINSTALLER
echo [4/4] Building .exe with PyInstaller (legacy path, higher AV FP rate)...
echo        For fewer antivirus false positives, re-run without --pyinstaller.
echo.

REM PyInstaller flags tuned to reduce (but not eliminate) AV false positives:
REM   --noupx  : never apply UPX compression (UPX-packed binaries are heavily flagged)
REM   --clean  : wipe PyInstaller cache before build for reproducibility
REM   --version-file : embed proper PE VERSIONINFO resource
pyinstaller ^
    --onefile ^
    --noconsole ^
    --noupx ^
    --clean ^
    --name AutoWarmUp ^
    --icon=app.ico ^
    --version-file=version_info.txt ^
    auto_warm_up.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
goto DONE


:DONE
echo.
echo ============================================================
echo  BUILD COMPLETE!
echo  Builder used: %BUILDER%
echo  Your .exe is at:  dist\AutoWarmUp.exe
echo.
echo  NOTE ON CODE SIGNING:
echo    This script intentionally does NOT self-sign the .exe.
echo    A self-signed signature HURTS antivirus reputation --
echo    AV engines treat "unknown publisher" signatures as more
echo    suspicious than an unsigned binary. To sign with a real
echo    CA-issued code-signing certificate, use sign_exe.sh with
echo    CODESIGN_PFX_BASE64 + CODESIGN_PFX_PASSWORD set.
echo ============================================================
echo.
pause
endlocal
