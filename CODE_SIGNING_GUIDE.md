# File Juggler — Code Signing, SmartScreen & Security Guide

This guide details how digital signatures, Microsoft Defender SmartScreen reputation, and code signing certificates operate for **File Juggler**, and provides instructions for both developers and end-users.

---

## 1. Understanding Windows Defender & SmartScreen Warnings

When users download and run a newly distributed Windows application, Microsoft Defender SmartScreen may display:

```text
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.
Running this app might put your PC at risk.
```

### Why SmartScreen Appears
1. **Unsigned Binary**: Executables without an Authenticode digital signature are immediately treated as untrusted.
2. **Missing Security Manifest**: Applications missing `<trustInfo>` or `<requestedExecutionLevel>` trigger legacy UAC virtualization heuristics.
3. **Reputation-Based Filtering**: Even signed applications require time to build download reputation with Microsoft's cloud telemetry unless signed with an **EV (Extended Validation)** Code Signing Certificate.

---

## 2. Solutions Implemented in File Juggler

### A. Security Manifest (`app.manifest`)
The application includes a certified Windows security manifest with:
```xml
<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
  <security>
    <requestedPrivileges>
      <requestedExecutionLevel level="asInvoker" uiAccess="false" />
    </requestedPrivileges>
  </security>
</trustInfo>
```
This certifies to Windows that File Juggler runs with standard user rights and does not perform unmanaged system-level virtualization.

### B. Automated Code Signing Tool (`scripts/sign_binaries.ps1`)
The project includes automated Authenticode code signing:
- Automatically creates and uses a dedicated SHA-256 Code Signing Certificate (`CN=File Juggler Software`).
- Applies cryptographic digital signatures to:
  - `dist\FileJuggler\FileJuggler.exe`
  - `dist\installer\FileJuggler_Setup_v1.0.0.exe`
- Incorporates RFC 3161 compliant timestamping (`http://timestamp.digicert.com`), ensuring signatures remain valid even after certificate expiration.
- Exports the public certificate `FileJuggler_Certificate.cer`.

---

## 3. How to Eliminate SmartScreen Warnings

### Method 1: One-Click Local Trust (Recommended for Testers/Users)
In the installer release directory:
1. Double-click:
   ```text
   dist\installer\Install-Certificate.bat
   ```
   *(or run `Install-Certificate.bat` in the repository root)*
2. This imports the certificate into the Windows **Trusted Publishers** and **Trusted Root Certification Authorities** store.
3. Windows Defender SmartScreen will immediately recognize File Juggler as a trusted publisher and suppress the warning screen.

---

### Method 2: Standard End-User Bypass ("Run anyway")
If an end user runs the setup without importing the certificate:
1. When the blue **"Windows protected your PC"** screen appears, click the underlined text: **"More info"**.
2. Click the button: **"Run anyway"**.
3. The installer wizard will launch normally.

*(Alternatively, users can right-click the `.exe` → **Properties** → check **"Unblock"** at the bottom → click **OK**).*

---

### Method 3: Commercial Code Signing Certificate (For Global Production)

To eliminate SmartScreen warnings worldwide without requiring users to trust a certificate, acquire a commercial Authenticode certificate from a WebTrust-audited Certificate Authority (CA):

#### Recommended Certificate Authorities:
- **DigiCert** (Standard or EV Code Signing)
- **Sectigo** (Standard or EV Code Signing)
- **Certum** (Cloud-based SimplySign / Hardware Token)
- **SSL.com** (eSigner Cloud HSM)

#### CA/Browser Forum Token Requirement:
Under current CA/Browser Forum security requirements, all code-signing private keys must be stored on a FIPS 140-2 Level 2 compliant hardware cryptographic token (such as a YubiKey) or a Cloud Hardware Security Module (HSM) such as Azure Key Vault or AWS CloudHSM.

#### Signing with a Commercial PFX or Hardware Token:
Run:
```powershell
.\scripts\sign_binaries.ps1 -CertificatePath "C:\path\to\YourCommercialCert.pfx" -Password "YourPassword"
```
Or using Microsoft's Windows SDK `signtool.exe`:
```cmd
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "dist\installer\FileJuggler_Setup_v1.0.0.exe"
```
Applications signed with an **EV (Extended Validation)** certificate gain **instant reputation** in Windows SmartScreen, bypassing all warnings from day one.
