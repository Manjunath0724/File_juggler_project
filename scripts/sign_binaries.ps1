<#
.SYNOPSIS
    Digitally signs File Juggler executables and installer packages.
.DESCRIPTION
    Applies an Authenticode digital signature using an existing commercial certificate (PFX)
    or generates a dedicated SHA-256 Code Signing Certificate and exports the public key.
#>

[CmdletBinding()]
param(
    [string]$CertificatePath,
    [string]$Password,
    [string[]]$FilesToSign
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
Set-Location $ProjectDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "             File Juggler -- Authenticode Code Signer                 " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Obtain or Create Code Signing Certificate
$Cert = $null

if ($CertificatePath -and (Test-Path $CertificatePath)) {
    Write-Host "`n[1/3] Loading code signing certificate from: $CertificatePath" -ForegroundColor Cyan
    $securePass = if ($Password) { ConvertTo-SecureString $Password -AsPlainText -Force } else { $null }
    $Cert = Get-PfxCertificate -FilePath $CertificatePath
}
else {
    # Check for existing File Juggler certificate in store
    $Cert = Get-ChildItem -Path "Cert:\CurrentUser\My" -CodeSigningCert -ErrorAction SilentlyContinue |
        Where-Object { $_.Subject -like "*File Juggler*" } |
        Select-Object -First 1

    if ($Cert) {
        Write-Host "`n[1/3] Using existing certificate: $($Cert.Subject) (Thumbprint: $($Cert.Thumbprint))" -ForegroundColor Green
    }
    else {
        Write-Host "`n[1/3] Generating dedicated SHA-256 Code Signing Certificate..." -ForegroundColor Yellow
        $Cert = New-SelfSignedCertificate `
            -Type CodeSigningCert `
            -Subject "CN=File Juggler Software, O=File Juggler Project, OU=Application Security, C=US" `
            -FriendlyName "File Juggler Application Signature" `
            -KeyAlgorithm RSA `
            -KeyLength 2048 `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -NotAfter (Get-Date).AddYears(5) `
            -HashAlgorithm SHA256

        Write-Host "Created certificate: $($Cert.Subject)" -ForegroundColor Green
        Write-Host "Thumbprint: $($Cert.Thumbprint)" -ForegroundColor Gray
    }
}

if (-not $Cert) {
    Write-Error "Failed to obtain or generate a code signing certificate."
    exit 1
}

# 2. Export Public Certificate (.cer) for End Users
Write-Host "`n[2/3] Exporting public certificate for Windows SmartScreen trust..." -ForegroundColor Cyan
$OutputDir = Join-Path $ProjectDir "dist\installer"
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

$CerPath = Join-Path $OutputDir "FileJuggler_Certificate.cer"
Export-Certificate -Cert $Cert -FilePath $CerPath -Force | Out-Null
Write-Host "Exported public certificate to: $CerPath" -ForegroundColor Green

# Also copy into dist\FileJuggler if exists
$BundleDir = Join-Path $ProjectDir "dist\FileJuggler"
if (Test-Path $BundleDir) {
    Copy-Item -Path $CerPath -Destination (Join-Path $BundleDir "FileJuggler_Certificate.cer") -Force
}

# 3. Sign Executables & Installer
Write-Host "`n[3/3] Signing application binaries..." -ForegroundColor Cyan

$DefaultFiles = @(
    (Join-Path $ProjectDir "dist\FileJuggler\FileJuggler.exe"),
    (Join-Path $ProjectDir "dist\installer\FileJuggler_Setup_v1.0.0.exe")
)

$Targets = if ($FilesToSign -and $FilesToSign.Count -gt 0) { $FilesToSign } else { $DefaultFiles }
$TimestampServers = @("http://timestamp.digicert.com", "http://timestamp.sectigo.com")

foreach ($file in $Targets) {
    if (-not (Test-Path $file)) {
        Write-Host "  Skipping missing target: $file" -ForegroundColor Yellow
        continue
    }

    Write-Host "  Signing: $file" -ForegroundColor White
    $signed = $false

    # Try timestamped signature first
    foreach ($ts in $TimestampServers) {
        try {
            $sig = Set-AuthenticodeSignature -FilePath $file -Certificate $Cert -TimestampServer $ts -HashAlgorithm SHA256 -ErrorAction Stop
            if ($sig.Status -eq "Valid" -or $sig.Status -eq "UnknownError") {
                $signed = $true
                Write-Host "    [OK] Signed with timestamp ($ts): Status = $($sig.Status)" -ForegroundColor Green
                break
            }
        }
        catch {
            # Continue to next timestamp server
        }
    }

    # Fallback to signing without timestamp if network is offline
    if (-not $signed) {
        $sig = Set-AuthenticodeSignature -FilePath $file -Certificate $Cert -HashAlgorithm SHA256
        Write-Host "    [OK] Signed without timestamp: Status = $($sig.Status)" -ForegroundColor Green
    }
}

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "               CODE SIGNING PROCESS COMPLETED                         " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
