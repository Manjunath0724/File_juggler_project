"""Progress dialog showing real-time file organization status."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
)


class ProgressDialog(QDialog):
    """Modal displaying moving progress with cancellation option."""

    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Files...")
        self.setModal(True)
        self.setFixedWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Title
        self.title_lbl = QLabel("Relocating and Organizing Files...")
        self.title_lbl.setProperty("class", "title")
        self.title_lbl.setStyleSheet("font-size: 17px; font-weight: 700;")
        layout.addWidget(self.title_lbl)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status counts & current file
        self.count_lbl = QLabel("Initializing operation...")
        self.count_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #3b82f6;")
        layout.addWidget(self.count_lbl)

        self.file_lbl = QLabel("")
        self.file_lbl.setProperty("class", "card-desc")
        self.file_lbl.setStyleSheet("font-size: 12px;")
        self.file_lbl.setWordWrap(True)
        layout.addWidget(self.file_lbl)

        # Cancel button
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.cancel_btn = QPushButton("Abort Operation")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_box.addWidget(self.cancel_btn)

        layout.addLayout(btn_box)

    def update_progress(self, current: int, total: int, filename: str, status_msg: str):
        """Update progress values and status message."""
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.count_lbl.setText(f"{current} of {total} files completed ({percent}%)")
        self.file_lbl.setText(f"Active: {filename}")

    def _on_cancel_clicked(self):
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Aborting...")
        self.cancel_requested.emit()
