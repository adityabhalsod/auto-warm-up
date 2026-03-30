@echo off
REM ============================================================
REM  Build script: compiles auto_warm_up.py into a standalone .exe
REM  with proper icon, PE version info, and self-signed certificate.
REM  Run this on your Windows 11 machine.
REM ============================================================

echo.
echo === Auto Warm-Up Build Script ===
echo.

REM Step 1: Install dependencies (user-level, no admin needed)
echo [1/5] Installing dependencies...
pip install --user -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

REM Step 2: Generate the multi-size .ico icon file using Pillow
echo [2/5] Generating application icon...
python generate_icon.py app.ico
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Icon generation failed.
    pause
    exit /b 1
)

REM Step 3: Generate PE version info from the VERSION file
echo [3/5] Generating version info...
python generate_version_info.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Version info generation failed.
    pause
    exit /b 1
)

REM Step 4: Build the .exe with icon and version info embedded
echo [4/5] Building .exe with PyInstaller...
pyinstaller --onefile --noconsole --name AutoWarmUp --icon=app.ico --version-file=version_info.txt auto_warm_up.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

REM Step 5: Self-sign the .exe if signtool is available (optional on Windows)
echo [5/5] Attempting to sign .exe...
where signtool >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    REM Generate a self-signed certificate and sign the .exe
    powershell -Command "if (-not (Test-Path cert:\CurrentUser\My\AutoWarmUp)) { $cert = New-SelfSignedCertificate -Subject 'CN=Aditya Bhalsod, O=Auto Warm-Up' -Type CodeSigningCert -CertStoreLocation Cert:\CurrentUser\My; }"
    for /f %%i in ('powershell -Command "(Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1).Thumbprint"') do set THUMBPRINT=%%i
    if defined THUMBPRINT (
        signtool sign /sha1 %THUMBPRINT% /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /d "Auto Warm-Up" dist\AutoWarmUp.exe
        echo   Signed successfully!
    ) else (
        echo   Skipped: No code signing certificate found.
    )
) else (
    echo   Skipped: signtool not found. Install Windows SDK for signing support.
)

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo  Your .exe is at:  dist\AutoWarmUp.exe
echo  Copy it anywhere and double-click to run.
echo ============================================================
echo.
pause
