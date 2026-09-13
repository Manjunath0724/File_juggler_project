"""Confirmation dialog presented before file movements are executed."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)

from src.utils.size_utils import format_size
from src.ui.theme import apply_card_shadow


class ConfirmDialog(QDialog):
    """Safety confirmation modal explaining exactly what will occur."""

    def __init__(self, file_count: int, total_bytes: int, category_count: int, is_dry_run: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm File Relocation" if not is_dry_run else "Confirm Simulation")
        self.setModal(True)
        self.setFixedWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header
        header_box = QVBoxLayout()
        header_box.setSpacing(6)

        status_tag = QLabel("[SIMULATION MODE]" if is_dry_run else "[ACTION REQUIRED]")
        status_tag.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #3b82f6; letter-spacing: 0.5px;"
            if is_dry_run else
            "font-size: 11px; font-weight: 700; color: #f59e0b; letter-spacing: 0.5px;"
        )

        title = QLabel("Confirm File Relocation" if not is_dry_run else "Confirm Dry-Run Simulation")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        header_box.addWidget(status_tag)
        header_box.addWidget(title)
        layout.addLayout(header_box)

        # Message Body Card
        body_frame = QFrame()
        body_frame.setProperty("class", "card")
        b_layout = QVBoxLayout(body_frame)
        b_layout.setSpacing(12)

        action_text = "simulate reorganizing" if is_dry_run else "relocate"
        msg = QLabel(
            f"File Juggler will {action_text} <b>{file_count} files</b> "
            f"({format_size(total_bytes)}) across <b>{category_count} categories</b>."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; line-height: 1.5;")

        safety_note = QLabel(
            "<b>Safety Assurance:</b> Zero-data-loss design. Files are never deleted, duplicate collisions "
            "are safely renamed, and operations can be undone with a single click."
        )
        safety_note.setWordWrap(True)
        safety_note.setStyleSheet("font-size: 12px; color: #10b981; line-height: 1.4;")

        b_layout.addWidget(msg)
        b_layout.addWidget(safety_note)
        layout.addWidget(body_frame)
        apply_card_shadow(body_frame, "dark")

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Execute Simulation" if is_dry_run else "Proceed with Organization")
        ok_btn.setProperty("class", "primary")
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)

        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)
