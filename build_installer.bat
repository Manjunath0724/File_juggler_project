@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo           File Juggler -- Windows Installer Build Tool
echo ======================================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%build_installer.ps1" %*

if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed or compiler was not found.
    pause
    exit /b 1
)

echo.
pause
exit /b 0
