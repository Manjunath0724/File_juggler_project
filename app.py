"""Application entrypoint for File Juggler."""
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Explicit Windows AppUserModelID for taskbar icon binding
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FileJuggler.Desktop.1.0")
    except Exception:
        pass

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.services.settings_service import get_config_dir
from src.ui.main_window import MainWindow


def get_resource_path(relative_path: str) -> Path:
    """Resolve absolute path to resource for dev or PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


def apply_native_windows_icons(hwnd: int, ico_path: Path):
    """Explicitly assign Win32 WM_SETICON on HWND for reliable Windows Taskbar icon display."""
    if sys.platform != "win32" or not ico_path.exists():
        return
    try:
        import ctypes
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010

        # Load 32x32 (taskbar/Alt+Tab) and 16x16 (titlebar) handles directly from multi-res .ico
        hicon_big = ctypes.windll.user32.LoadImageW(
            None, str(ico_path.resolve()), IMAGE_ICON, 32, 32, LR_LOADFROMFILE
        )
        hicon_small = ctypes.windll.user32.LoadImageW(
            None, str(ico_path.resolve()), IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )
        if hicon_big:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
        if hicon_small:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
    except Exception:
        pass


def main():
    import logging

    try:
        log_dir = get_config_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "app.log"
    except Exception:
        log_path = Path.cwd() / "app.log"

    logging.basicConfig(
        filename=str(log_path),
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        encoding="utf-8"
    )
    logging.info("Starting File Juggler application...")

    try:
        # High DPI scaling configuration
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("File Juggler")
        app.setApplicationDisplayName("File Juggler")
        app.setOrganizationName("FileJuggler")

        # Prioritize multi-resolution Windows .ico container (contains 16, 32, 48, 64, 128, 256px)
        ico_path = get_resource_path("assets/icon.ico")
        png_path = get_resource_path("assets/icon.png")

        if ico_path.exists():
            app_icon = QIcon(str(ico_path))
        elif png_path.exists():
            app_icon = QIcon(str(png_path))
        else:
            app_icon = QIcon()

        if not app_icon.isNull():
            app.setWindowIcon(app_icon)

        # Base typography
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        app.setFont(font)

        logging.info("Initializing MainWindow...")
        window = MainWindow()
        if not app_icon.isNull():
            window.setWindowIcon(app_icon)
        window.show()

        # Apply native Win32 window class and taskbar icons
        if ico_path.exists():
            apply_native_windows_icons(int(window.winId()), ico_path)

        # System Tray Icon integration (displays alongside WhatsApp in Notification Area)
        tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable() and not app_icon.isNull():
            tray_icon = QSystemTrayIcon(app_icon, parent=window)
            tray_icon.setToolTip("File Juggler — Smart Desktop File Organizer")

            tray_menu = QMenu()
            show_action = QAction("Open File Juggler", window)
            show_action.triggered.connect(lambda: (window.showNormal(), window.activateWindow(), window.raise_()))
            tray_menu.addAction(show_action)

            tray_menu.addSeparator()
            quit_action = QAction("Exit", window)
            quit_action.triggered.connect(app.quit)
            tray_menu.addAction(quit_action)

            tray_icon.setContextMenu(tray_menu)
            tray_icon.activated.connect(
                lambda reason: (window.showNormal(), window.activateWindow(), window.raise_())
                if reason == QSystemTrayIcon.ActivationReason.Trigger else None
            )
            tray_icon.show()

        logging.info("MainWindow displayed. Entering Qt main event loop...")
        exit_code = app.exec()
        logging.info(f"Application event loop ended with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        import traceback
        logging.error(f"Fatal crash in main(): {e}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
