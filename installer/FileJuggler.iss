; =====================================================================
; File Juggler -- Inno Setup Script
; Commercial-grade Windows installer script
; =====================================================================

#define MyAppName "File Juggler"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "File Juggler Team"
#define MyAppURL "https://github.com/filejuggler/filejuggler"
#define MyAppExeName "FileJuggler.exe"
#define MyAppId "{{8E587522-8B23-41A8-A216-95AC57E12D34}"

[Setup]
; Unique application GUID for update detection and clean uninstall
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination directories: 64-bit Program Files by default on 64-bit systems
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\File Juggler
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt

; Output installer artifact settings
OutputDir=..\dist
OutputBaseFilename=FileJuggler_Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#MyAppName}

; Compression settings for minimal installer size and fast extraction
Compression=lzma2/max
SolidCompression=yes

; Modern visual styling
WizardStyle=modern
WizardResizable=no
DisableWelcomePage=no

; Administrative privileges required for C:\Program Files installation
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Clean update / installation behavior
CloseApplications=yes
RestartApplications=no
DirExistsWarning=yes
EnableDirDoesntExistWarning=yes
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startupicon"; Description: "Launch File Juggler automatically when Windows starts"; GroupDescription: "System Startup:"; Flags: unchecked
Name: "contextmenu"; Description: "Add 'Organize with File Juggler' to Windows Explorer folder right-click menu"; GroupDescription: "Windows Explorer Integration:"; Flags: checkedonce

[Files]
; Recursively package the compiled PyInstaller bundle
Source: "..\dist\FileJuggler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ensure high-res icon and license are available in install root
Source: "..\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"; WorkingDir: "{app}"; AppUserModelID: "FileJuggler.Desktop.1.0"
; Start Menu Shortcuts
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon; IconFilename: "{app}\assets\icon.ico"; WorkingDir: "{app}"; AppUserModelID: "FileJuggler.Desktop.1.0"
Name: "{autoprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon; WorkingDir: "{app}"

[Registry]
; Register application in Windows App Paths (allows Win+R -> FileJuggler)
; HKA automatically maps to HKLM (all users/admin) or HKCU (current user)
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

; Optional: Windows Startup Run key
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FileJuggler"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startupicon; Flags: uninsdeletevalue

; Optional: Folder Context Menu Integration
Root: HKA; Subkey: "Software\Classes\Directory\shell\FileJuggler"; ValueType: string; ValueName: ""; ValueData: "Organize with File Juggler"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Directory\shell\FileJuggler"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\assets\icon.ico"""; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Directory\shell\FileJuggler\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu; Flags: uninsdeletekey

[Run]
; Option on completion screen to immediately launch the application
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up runtime logs and temporary caches created by the application
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\app.log"

[Code]
// Optional Pascal code for pre-install validation
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
