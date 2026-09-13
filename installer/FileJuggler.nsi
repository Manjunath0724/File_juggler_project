; =====================================================================
; File Juggler -- NSIS (Nullsoft Scriptable Install System) Script
; Modern UI 2 Installer Configuration
; =====================================================================

Unicode True

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; General Configuration
!define PRODUCT_NAME "File Juggler"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "File Juggler Team"
!define PRODUCT_WEB_SITE "https://github.com/filejuggler/filejuggler"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\FileJuggler.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\dist\installer\FileJuggler_Setup_NSIS_v${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\File Juggler"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel admin

; Visual Styling
SetCompressor /SOLID lzma
!define MUI_ABORTWARNING
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

; Installer Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Finish Page with Run Application option
!define MUI_FINISHPAGE_RUN "$INSTDIR\FileJuggler.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch File Juggler"
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; ---------------------------------------------------------------------
; Component Sections
; ---------------------------------------------------------------------

Section "!Core Application Files" SEC01
    SectionIn RO ; Read-only (required)
    SetOutPath "$INSTDIR"
    SetOverwrite on

    ; Copy compiled bundle
    File /r "..\dist\FileJuggler\*.*"
    
    ; Create assets directory and copy icon
    CreateDirectory "$INSTDIR\assets"
    File /oname=assets\icon.ico "..\assets\icon.ico"
    File /oname=assets\icon.png "..\assets\icon.png"
    File "..\LICENSE.txt"

    ; Write Uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Register in Windows App Paths (for Run dialog)
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\FileJuggler.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"

    ; Register in Control Panel Add/Remove Programs
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\assets\icon.ico"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"

    ; Compute estimated size for Control Panel
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "Start Menu Shortcut" SEC02
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\FileJuggler.exe" "" "$INSTDIR\assets\icon.ico" 0
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

Section "Desktop Shortcut" SEC03
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\FileJuggler.exe" "" "$INSTDIR\assets\icon.ico" 0
SectionEnd

Section "Folder Context Menu Integration" SEC04
    WriteRegStr HKCR "Directory\shell\FileJuggler" "" "Organize with File Juggler"
    WriteRegStr HKCR "Directory\shell\FileJuggler" "Icon" "$INSTDIR\assets\icon.ico"
    WriteRegStr HKCR "Directory\shell\FileJuggler\command" "" '"$INSTDIR\FileJuggler.exe" "%1"'
SectionEnd

; Component Descriptions
LangString DESC_SEC01 ${LANG_ENGLISH} "Core binary files and dependencies required to run File Juggler."
LangString DESC_SEC02 ${LANG_ENGLISH} "Adds File Juggler and Uninstaller to your Windows Start Menu."
LangString DESC_SEC03 ${LANG_ENGLISH} "Creates a quick-access shortcut on your Desktop."
LangString DESC_SEC04 ${LANG_ENGLISH} "Adds 'Organize with File Juggler' to folder right-click context menus."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} $(DESC_SEC01)
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} $(DESC_SEC02)
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} $(DESC_SEC03)
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC04} $(DESC_SEC04)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ---------------------------------------------------------------------
; Uninstallation Section
; ---------------------------------------------------------------------

Section "Uninstall"
    ; Remove Context menu entry
    DeleteRegKey HKCR "Directory\shell\FileJuggler"

    ; Remove App Paths
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

    ; Remove Control Panel Entry
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"

    ; Remove Shortcuts
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

    ; Remove Application Files and Directories
    RMDir /r "$INSTDIR"

    SetAutoClose false
SectionEnd
