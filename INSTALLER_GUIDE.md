# File Juggler — Windows Installer Guide & Distribution Reference

This guide provides complete instructions for building, customizing, and distributing the professional Windows installer for **File Juggler**.

---

## 1. Overview & Architecture

File Juggler uses **Inno Setup 6** (with an alternative **NSIS** configuration) to produce a single-file, production-grade Windows setup installer:

```text
dist/installer/FileJuggler_Setup_v1.0.0.exe
```

The installer behaves like standard commercial software (similar to VS Code, Git for Windows, or 7-Zip), providing an intuitive step-by-step wizard, Windows shell integration, Control Panel registration, and a clean uninstaller.

---

## 2. Requirements Compliance Matrix

| Requirement | Implementation in Inno Setup (`installer/FileJuggler.iss`) |
|---|---|
| **1. Welcome Screen** | Displays application name ("File Juggler"), version ("1.0.0"), and publisher information (`DisableWelcomePage=no`). |
| **1. License Agreement** | Displays [LICENSE.txt](file:///c:/Users/asus/Desktop/File_juggler_projec/LICENSE.txt) with "I accept the agreement" radio button before proceeding (`LicenseFile=..\LICENSE.txt`). |
| **1. Destination Folder** | Defaults to `C:\Program Files\File Juggler` on 64-bit Windows (`ArchitecturesInstallIn64BitMode=x64compatible`, `DefaultDirName={autopf}\File Juggler`) with custom Browse folder selection and disk space checking. |
| **1. Components / Tasks** | Interactive checkboxes for Desktop Shortcut, Start Menu Shortcut, Windows Startup run, and Windows Explorer folder context menu. |
| **1. Progress Tracking** | Animated progress bar showing real-time file extraction, status, and overall percentage. |
| **1. Completion Screen** | "Completing the File Juggler Setup Wizard" confirmation with a "Launch File Juggler" checkbox (`postinstall skipifsilent`). |
| **2. File Installation** | Recursively copies all binaries from `dist\FileJuggler\*` (main executable, `_internal\`, Qt runtime, assets, license) into `{app}`. |
| **3. Desktop Icon** | Creates a functional desktop shortcut `{autodesktop}\File Juggler.lnk` with `{app}\assets\icon.ico` and correct working directory. |
| **4. Start Menu Integration** | Creates `{autoprograms}\File Juggler\File Juggler.lnk` and `{autoprograms}\File Juggler\Uninstall File Juggler.lnk`. |
| **4. Control Panel Registration** | Registers in `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\{8E587522...}` with `DisplayName`, `DisplayVersion`, `Publisher`, `DisplayIcon`, and `UninstallString`. |
| **4. Uninstaller Program** | Generates native uninstaller (`unins000.exe`) in `{app}` that cleanly removes binaries, shortcuts, and registry entries. |
| **5. Running Process Check** | `CloseApplications=yes` safely prompts the user to close any running instances of File Juggler before installation or upgrade. |
| **5. Run Dialog Shortcut** | Registers `App Paths\FileJuggler.exe` so users can press `Win + R` and type `FileJuggler` to launch the app. |

---

## 3. Quick Start: How to Build the Installer

> [!TIP]
> **Zero External Setup Required**: The repository includes a portable Inno Setup 6 compiler in `tools/InnoSetup/ISCC.exe`. You can compile the installer immediately without installing any third-party tools or package managers!

### How to Compile the Installer

#### Method A: Using the Automated Batch Script
Double-click `build_installer.bat` in Windows Explorer, or run in Command Prompt:
```cmd
build_installer.bat
```
*(In PowerShell, prefix with `.\`: `.\build_installer.bat`)*

#### Method B: Using PowerShell
Run in your PowerShell terminal:
```powershell
.\build_installer.ps1
```

If you already built the PyInstaller bundle and want to skip re-building it:
```powershell
.\build_installer.ps1 -SkipBuild
```

#### Method C: Using the Inno Setup GUI Compiler
1. Open **Inno Setup Compiler** from your Start Menu.
2. Click **File → Open** and select:
   ```text
   File_juggler_projec\installer\FileJuggler.iss
   ```
3. Click **Build → Compile** (or press `Ctrl + F9`).
4. The compiled installer executable will be saved in `dist\installer\FileJuggler_Setup_v1.0.0.exe`.

---

## 4. Alternative: Building with NSIS

An equivalent NSIS script using Modern UI 2 is provided in [installer/FileJuggler.nsi](file:///c:/Users/asus/Desktop/File_juggler_projec/installer/FileJuggler.nsi).

To build using NSIS:
1. Install NSIS:
   ```powershell
   winget install NSIS.NSIS
   ```
2. Run:
   ```powershell
   .\build_installer.ps1 -Engine NSIS
   ```
   Or right-click `installer\FileJuggler.nsi` and select **Compile NSIS Script**.

---

## 5. Command-Line & Silent Installation Parameters

The generated installer supports standard Windows command-line flags for automated deployments, CI/CD, and system administrators:

| Parameter | Description |
|---|---|
| `/SILENT` | Displays the wizard and progress bar, but does not wait for user clicks. |
| `/VERYSILENT` | Installs completely in the background with no wizard or progress window. |
| `/SUPPRESSMSGBOXES` | Suppresses any message boxes during silent installation. |
| `/NORESTART` | Prevents rebooting even if system files were replaced. |
| `/DIR="D:\CustomPath"` | Overrides the default install folder (`C:\Program Files\File Juggler`). |
| `/TASKS="desktopicon"` | Selects specific tasks (comma-separated). |

### Example Silent Install Command:
```cmd
FileJuggler_Setup_v1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

---

## 6. Uninstallation Behavior

When users uninstall File Juggler:
1. Open Windows **Settings → Apps → Installed apps** (or classic **Control Panel → Programs and Features**).
2. Find **File Juggler** in the list and click **Uninstall**.
3. The uninstaller:
   - Confirms uninstallation with the user.
   - Checks and prompts to close any running instances of `FileJuggler.exe`.
   - Removes all installed files from `C:\Program Files\File Juggler`.
   - Cleans up Desktop and Start Menu shortcuts.
   - Removes Control Panel and App Paths registry entries.
   - Deletes temporary logs (`app.log`) and cache folders.
   - Removes the empty installation folder.

---

## 7. Commercial Distribution & Code Signing

Before publishing your installer to public users or website downloads, it is recommended to sign both `FileJuggler.exe` and `FileJuggler_Setup_v1.0.0.exe` using a valid Microsoft Authenticode code signing certificate. This avoids Windows SmartScreen "Unknown Publisher" warnings.

To sign using Windows SDK `signtool.exe`:
```cmd
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "dist\installer\FileJuggler_Setup_v1.0.0.exe"
```
In Inno Setup, you can also automate signing during compilation by adding the `SignTool` directive in `[Setup]`.
