# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for a single standalone portable executable."""
import os
import sys
from pathlib import Path

block_cipher = None
project_dir = os.path.abspath(os.curdir)

datas = [
    ('assets', 'assets'),
    ('LICENSE.txt', '.'),
]

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'shiboken6',
    'src.core.scanner',
    'src.core.classifier',
    'src.core.organizer',
    'src.core.duplicate_handler',
    'src.core.undo_manager',
    'src.models.file_item',
    'src.models.organization_rule',
    'src.models.operation_result',
    'src.services.settings_service',
    'src.services.history_service',
    'src.services.logging_service',
    'src.services.encryption_service',
    'src.ui.theme',
    'src.ui.main_window',
    'src.ui.views.setup_view',
    'src.ui.views.preview_view',
    'src.ui.views.results_view',
    'src.ui.dialogs.confirm_dialog',
    'src.ui.dialogs.progress_dialog',
    'src.ui.dialogs.settings_dialog',
    'src.ui.dialogs.history_dialog',
    'src.utils.file_utils',
    'src.utils.size_utils',
]

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'unittest',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileJuggler_Standalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    manifest='app.manifest',
)
