@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo           File Juggler -- Standalone Windows Executable Build
echo ======================================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM 1. Check Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Please create the virtual environment and install requirements first:
    echo     python -m venv .venv
    echo     .\.venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

set "PYTHON=.venv\Scripts\python.exe"
set "PYINSTALLER=.venv\Scripts\pyinstaller.exe"

REM 2. Ensure PyInstaller is installed
if not exist "%PYINSTALLER%" (
    echo [INFO] PyInstaller not detected in virtualenv. Installing...
    "%PYTHON%" -m pip install pyinstaller>=6.0.0
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)

REM 3. Run Automated Tests
echo [1/4] Running automated test suite...
"%PYTHON%" -m pytest tests/ -v --color=yes
if errorlevel 1 (
    echo.
    echo [ERROR] Test suite failed! Aborting build to ensure package stability.
    exit /b 1
)
echo [1/4] All tests passed successfully.
echo.

REM 4. Ensure Application Icons Exist
echo [2/4] Verifying application assets and icons...
if not exist "assets\icon.ico" (
    echo Generating multi-resolution icon assets...
    "%PYTHON%" scripts\generate_icon.py
    if errorlevel 1 (
        echo [ERROR] Failed to generate icon assets.
        exit /b 1
    )
)
echo [2/4] Assets verified.
echo.

REM 5. Run PyInstaller
echo [3/4] Building standalone Windows executable with PyInstaller...
"%PYINSTALLER%" --clean --noconfirm FileJuggler.spec
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)
echo [3/4] Packaging complete.
echo.

REM 6. Validate Build Artifacts
echo [4/4] Validating output bundle...
if not exist "dist\FileJuggler\FileJuggler.exe" (
    echo [ERROR] Expected binary not found at dist\FileJuggler\FileJuggler.exe
    exit /b 1
)

echo.
echo ======================================================================
echo                       BUILD SUCCESSFUL!
echo ======================================================================
echo Executable:  %PROJECT_DIR%dist\FileJuggler\FileJuggler.exe
echo Bundle Dir:  %PROJECT_DIR%dist\FileJuggler\
echo.
echo You can run the application directly by executing:
echo     .\dist\FileJuggler\FileJuggler.exe
echo ======================================================================

exit /b 0
