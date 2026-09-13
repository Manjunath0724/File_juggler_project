<#
.SYNOPSIS
    Builds the standalone Windows executable for File Juggler.
.DESCRIPTION
    Automates test execution, asset verification, and PyInstaller bundling
    into a self-contained folder at dist/FileJuggler/FileJuggler.exe.
#>

[CmdletBinding()]
param(
    [switch]$SkipTests = $false,
    [switch]$CleanOnly = $false
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          File Juggler -- Standalone Windows Executable Build          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if ($CleanOnly) {
    Write-Host "[INFO] Cleaning build and dist artifacts..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    Write-Host "Cleanup complete." -ForegroundColor Green
    return
}

# 1. Virtual environment paths
$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$PyInstallerExe = Join-Path $ProjectDir ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $PythonExe. Please set up .venv first."
    exit 1
}

# 2. Check PyInstaller
if (-not (Test-Path $PyInstallerExe)) {
    Write-Host "[INFO] Installing PyInstaller into virtual environment..." -ForegroundColor Yellow
    & $PythonExe -m pip install "pyinstaller>=6.0.0"
}

# 3. Run Test Suite
if (-not $SkipTests) {
    Write-Host "`n[1/4] Running automated test suite..." -ForegroundColor Cyan
    & $PythonExe -m pytest tests/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Test suite failed! Aborting build to protect release quality."
        exit $LASTEXITCODE
    }
    Write-Host "[1/4] Tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[1/4] Skipping test suite as requested." -ForegroundColor Yellow
}

# 4. Generate/Verify Icons
Write-Host "`n[2/4] Verifying application assets and icons..." -ForegroundColor Cyan
$IconPath = Join-Path $ProjectDir "assets\icon.ico"
if (-not (Test-Path $IconPath)) {
    Write-Host "Generating icon assets..." -ForegroundColor Yellow
    & $PythonExe (Join-Path $ProjectDir "scripts\generate_icon.py")
}
Write-Host "[2/4] Assets verified." -ForegroundColor Green

# 5. Run PyInstaller
Write-Host "`n[3/4] Building standalone Windows executable with PyInstaller..." -ForegroundColor Cyan
$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

& $PyInstallerExe --clean --noconfirm (Join-Path $ProjectDir "FileJuggler.spec")
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed!"
    exit $LASTEXITCODE
}
$Stopwatch.Stop()
Write-Host "[3/4] Packaging complete in $($Stopwatch.Elapsed.TotalSeconds.ToString('F1'))s." -ForegroundColor Green

# 6. Validate Output
Write-Host "`n[4/4] Validating output bundle..." -ForegroundColor Cyan
$ExePath = Join-Path $ProjectDir "dist\FileJuggler\FileJuggler.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "Expected binary not found at $ExePath"
    exit 1
}

$ExeItem = Get-Item $ExePath
$ExeSizeMB = ($ExeItem.Length / 1MB).ToString("F2")

# Calculate total bundle size
$BundleDir = Join-Path $ProjectDir "dist\FileJuggler"
$TotalBytes = (Get-ChildItem -Path $BundleDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
$BundleSizeMB = ($TotalBytes / 1MB).ToString("F2")

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "                       BUILD SUCCESSFUL!                              " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  Executable : $ExePath ($ExeSizeMB MB)" -ForegroundColor White
Write-Host "  Bundle Dir : $BundleDir ($BundleSizeMB MB total)" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
