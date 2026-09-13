<#
.SYNOPSIS
    Builds the professional Windows installer package for File Juggler.
.DESCRIPTION
    Automates building the standalone PyInstaller bundle (if needed) and compiling
    the final commercial-grade Windows setup installer using Inno Setup or NSIS.
.PARAMETER Engine
    Installer engine to use: 'InnoSetup' (default, recommended) or 'NSIS'.
.PARAMETER SkipBuild
    Skip running PyInstaller build if dist\FileJuggler\FileJuggler.exe already exists.
#>

[CmdletBinding()]
param(
    [ValidateSet("InnoSetup", "NSIS")]
    [string]$Engine = "InnoSetup",
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         File Juggler -- Windows Installer Package Builder            " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------
# 1. Verify PyInstaller Executable Bundle
# ---------------------------------------------------------------------
$AppExe = Join-Path $ProjectDir "dist\FileJuggler\FileJuggler.exe"
if (-not (Test-Path $AppExe) -or -not $SkipBuild) {
    if (-not (Test-Path $AppExe)) {
        Write-Host "`n[1/3] Application binary not found at $AppExe. Initiating build..." -ForegroundColor Yellow
        & (Join-Path $ProjectDir "build.ps1")
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build application binary with build.ps1"
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "`n[1/3] Standalone application bundle verified at: dist\FileJuggler" -ForegroundColor Green
    }
} else {
    Write-Host "`n[1/3] Using existing application bundle (-SkipBuild specified)." -ForegroundColor Green
}

# Sign application executable before packaging
$SignScript = Join-Path $ProjectDir "scripts\sign_binaries.ps1"
if (Test-Path $SignScript) {
    Write-Host "Signing application executable before packaging..." -ForegroundColor Cyan
    & $SignScript -FilesToSign @($AppExe)
}

# Ensure destination directory for installers
$InstallerOutputDir = Join-Path $ProjectDir "dist\installer"
if (-not (Test-Path $InstallerOutputDir)) {
    New-Item -ItemType Directory -Path $InstallerOutputDir -Force | Out-Null
}

# ---------------------------------------------------------------------
# 2. Locate Compiler Tools
# ---------------------------------------------------------------------
Write-Host "`n[2/3] Searching for installer compiler ($Engine)..." -ForegroundColor Cyan

function Find-InnoSetup {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Antigravity IDE\resources\app\node_modules\innosetup\bin\ISCC.exe"),
        (Join-Path $ProjectDir "tools\InnoSetup\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        "C:\Program Files\Inno Setup 5\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 5\ISCC.exe")
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command "iscc" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-NSIS {
    $candidates = @(
        "C:\Program Files (x86)\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command "makensis" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$IsccPath = Find-InnoSetup
$NsisPath = Find-NSIS

# ---------------------------------------------------------------------
# 3. Compile Installer
# ---------------------------------------------------------------------
if ($Engine -eq "InnoSetup") {
    if (-not $IsccPath) {
        Write-Host "`n[WARNING] Inno Setup compiler (ISCC.exe) was not found on your system." -ForegroundColor Yellow
        Write-Host "Inno Setup is required to compile the native .exe installer." -ForegroundColor White
        Write-Host "`nTo install Inno Setup, run one of the following commands in an elevated PowerShell/Terminal:" -ForegroundColor Cyan
        Write-Host "    winget install JRSoftware.InnoSetup" -ForegroundColor Green
        Write-Host "    choco install innosetup" -ForegroundColor Green
        Write-Host "Or download the official installer directly from: https://jrsoftware.org/isdl.php" -ForegroundColor Gray
        Write-Host "`nInstaller script is ready at: installer\FileJuggler.iss" -ForegroundColor Cyan
        exit 1
    }

    Write-Host "Found Inno Setup Compiler: $IsccPath" -ForegroundColor Green
    Write-Host "`n[3/3] Compiling installer package with Inno Setup..." -ForegroundColor Cyan

    $IssFile = Join-Path $ProjectDir "installer\FileJuggler.iss"
    $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    & $IsccPath $IssFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Inno Setup compilation failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    $Stopwatch.Stop()
    Write-Host "Compilation completed in $($Stopwatch.Elapsed.TotalSeconds.ToString('F1'))s." -ForegroundColor Green

    $ExpectedOutput = Join-Path $InstallerOutputDir "FileJuggler_Setup_v1.0.0.exe"
}
elseif ($Engine -eq "NSIS") {
    if (-not $NsisPath) {
        Write-Host "`n[WARNING] NSIS compiler (makensis.exe) was not found on your system." -ForegroundColor Yellow
        Write-Host "To install NSIS, run:" -ForegroundColor Cyan
        Write-Host "    winget install NSIS.NSIS" -ForegroundColor Green
        Write-Host "Or download from: https://nsis.sourceforge.io" -ForegroundColor Gray
        exit 1
    }

    Write-Host "Found NSIS Compiler: $NsisPath" -ForegroundColor Green
    Write-Host "`n[3/3] Compiling installer package with NSIS..." -ForegroundColor Cyan

    $NsiFile = Join-Path $ProjectDir "installer\FileJuggler.nsi"
    $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    & $NsisPath $NsiFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "NSIS compilation failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    $Stopwatch.Stop()
    Write-Host "Compilation completed in $($Stopwatch.Elapsed.TotalSeconds.ToString('F1'))s." -ForegroundColor Green

    $ExpectedOutput = Join-Path $InstallerOutputDir "FileJuggler_Setup_NSIS_v1.0.0.exe"
}

# ---------------------------------------------------------------------
# 4. Validate & Output Release Checksums
# ---------------------------------------------------------------------
if (Test-Path $ExpectedOutput) {
    # Sign final installer package
    if (Test-Path $SignScript) {
        Write-Host "`nDigitally signing installer package..." -ForegroundColor Cyan
        & $SignScript -FilesToSign @($ExpectedOutput)
    }

    $OutputItem = Get-Item $ExpectedOutput
    $SizeMB = ($OutputItem.Length / 1MB).ToString("F2")
    $Hash = (Get-FileHash -Path $ExpectedOutput -Algorithm SHA256).Hash

    Write-Host "`n======================================================================" -ForegroundColor Green
    Write-Host "                   INSTALLER BUILD SUCCESSFUL!                        " -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "  Installer File : $ExpectedOutput" -ForegroundColor White
    Write-Host "  File Size      : $SizeMB MB" -ForegroundColor White
    Write-Host "  SHA256 Hash    : $Hash" -ForegroundColor Gray
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "You can now distribute this setup executable to users." -ForegroundColor Cyan
} else {
    Write-Error "Installer compilation finished but expected artifact not found at $ExpectedOutput"
    exit 1
}
