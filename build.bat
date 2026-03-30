@echo off
REM ============================================================
REM  Build script: compiles auto_warm_up.py into a standalone .exe
REM  Run this on your Windows 11 machine.
REM ============================================================

echo.
echo === Auto Warm-Up Build Script ===
echo.

REM Step 1: Install dependencies (user-level, no admin needed)
echo [1/2] Installing dependencies...
pip install --user -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

REM Step 2: Build the .exe with PyInstaller (single file, no console window)
echo [2/2] Building .exe with PyInstaller...
pyinstaller --onefile --noconsole --name AutoWarmUp --icon=NONE auto_warm_up.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo  Your .exe is at:  dist\AutoWarmUp.exe
echo  Copy it anywhere and double-click to run.
echo ============================================================
echo.
pause
