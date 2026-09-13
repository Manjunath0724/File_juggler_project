"""Settings dialog for File Juggler preferences."""
from typing import Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QFrame
)

from src.services.settings_service import SettingsService
from src.ui.theme import apply_card_shadow


class SettingsDialog(QDialog):
    """User preferences configuration dialog."""

    settings_saved = Signal(dict)

    def __init__(self, settings_service: SettingsService, parent=None):
        super().__init__(parent)
        self.settings_service = settings_service
        self.setWindowTitle("File Juggler Preferences")
        self.setModal(True)
        self.setFixedWidth(480)

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Application Preferences")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        # Theme
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Interface Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark Mode", "dark")
        self.theme_combo.addItem("Light Mode", "light")
        theme_row.addWidget(self.theme_combo)
        card_layout.addLayout(theme_row)

        # Default Duplicate Policy
        dup_row = QHBoxLayout()
        dup_row.addWidget(QLabel("Default Collision Policy:"))
        self.dup_combo = QComboBox()
        self.dup_combo.addItem("Rename (photo (1).jpg)", "rename")
        self.dup_combo.addItem("Skip file", "skip")
        self.dup_combo.addItem("Replace file", "replace")
        dup_row.addWidget(self.dup_combo)
        card_layout.addLayout(dup_row)

        # Excluded Extensions
        ext_row = QVBoxLayout()
        ext_row.addWidget(QLabel("Global Excluded Extensions:"))
        self.ext_input = QLineEdit()
        ext_row.addWidget(self.ext_input)
        card_layout.addLayout(ext_row)

        # Excluded Folders
        folder_row = QVBoxLayout()
        folder_row.addWidget(QLabel("Global Excluded Folders:"))
        self.folder_input = QLineEdit()
        folder_row.addWidget(self.folder_input)
        card_layout.addLayout(folder_row)

        layout.addWidget(card)
        apply_card_shadow(card, "dark")

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Preferences")
        save_btn.setProperty("class", "primary")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)

        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _load_current_settings(self):
        settings = self.settings_service.load()
        # Theme
        idx = self.theme_combo.findData(settings.get("theme", "dark"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        # Duplicate
        d_idx = self.dup_combo.findData(settings.get("duplicate_policy", "rename"))
        if d_idx >= 0:
            self.dup_combo.setCurrentIndex(d_idx)

        # Exclusions
        exts = settings.get("excluded_extensions", [])
        self.ext_input.setText(", ".join(exts))

        folders = settings.get("excluded_folders", [])
        self.folder_input.setText(", ".join(folders))

    def _save_settings(self):
        settings = self.settings_service.load()
        settings["theme"] = self.theme_combo.currentData()
        settings["duplicate_policy"] = self.dup_combo.currentData()
        settings["excluded_extensions"] = [
            e.strip() for e in self.ext_input.text().split(",") if e.strip()
        ]
        settings["excluded_folders"] = [
            f.strip() for f in self.folder_input.text().split(",") if f.strip()
        ]

        self.settings_service.save(settings)
        self.settings_saved.emit(settings)
        self.accept()
