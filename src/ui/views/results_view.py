"""Results View: Summary of file organization metrics and undo capability."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QGridLayout
)

from src.models.operation_result import OperationResult
from src.ui.theme import apply_card_shadow


class ResultsView(QWidget):
    """View shown after an organization operation completes."""

    organize_another_requested = Signal()
    undo_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result: Optional[OperationResult] = None
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("resultsView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(44, 36, 44, 36)
        layout.setSpacing(26)

        # 1. Header with custom geometric success seal (No emojis)
        header_box = QVBoxLayout()
        header_box.setAlignment(Qt.AlignCenter)
        header_box.setSpacing(12)

        self.icon_badge = QLabel("✓")
        self.icon_badge.setStyleSheet(
            "font-size: 32px; font-weight: 800; color: #10b981; "
            "background-color: rgba(16, 185, 129, 0.12); border: 2px solid #10b981; "
            "border-radius: 36px; min-width: 72px; max-width: 72px; min-height: 72px; max-height: 72px;"
        )
        self.icon_badge.setAlignment(Qt.AlignCenter)

        self.title_lbl = QLabel("Organization Complete")
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #10b981;")
        self.title_lbl.setAlignment(Qt.AlignCenter)

        self.subtitle_lbl = QLabel("All eligible files have been relocated into clean directory structures.")
        self.subtitle_lbl.setProperty("class", "subtitle")
        self.subtitle_lbl.setAlignment(Qt.AlignCenter)

        header_box.addWidget(self.icon_badge, alignment=Qt.AlignCenter)
        header_box.addWidget(self.title_lbl)
        header_box.addWidget(self.subtitle_lbl)
        layout.addLayout(header_box)

        # 2. Stats Grid Card with 3D elevation
        self.stats_card = QFrame()
        self.stats_card.setProperty("class", "card")
        stats_layout = QGridLayout(self.stats_card)
        stats_layout.setContentsMargins(28, 24, 28, 24)
        stats_layout.setHorizontalSpacing(36)
        stats_layout.setVerticalSpacing(20)

        # Stat widgets
        self.moved_val = self._create_stat_widget(stats_layout, "Files Moved", "0", 0, 0, "#10b981")
        self.skipped_val = self._create_stat_widget(stats_layout, "Files Skipped", "0", 0, 1, "#f59e0b")
        self.failed_val = self._create_stat_widget(stats_layout, "Errors Encountered", "0", 1, 0, "#ef4444")
        self.duration_val = self._create_stat_widget(stats_layout, "Duration", "0.0s", 1, 1, "#3b82f6")

        layout.addWidget(self.stats_card)

        # Folder location notice
        self.dest_notice_lbl = QLabel("")
        self.dest_notice_lbl.setProperty("class", "card-desc")
        self.dest_notice_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.dest_notice_lbl)

        layout.addStretch()

        # 3. Action Buttons (Clean text, no emojis)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.open_dest_btn = QPushButton("Open Destination Directory")
        self.open_dest_btn.setProperty("class", "primary")
        self.open_dest_btn.setMinimumHeight(44)
        self.open_dest_btn.setCursor(Qt.PointingHandCursor)
        self.open_dest_btn.clicked.connect(self._open_destination)

        self.undo_btn = QPushButton("Rollback Changes (Undo)")
        self.undo_btn.setMinimumHeight(44)
        self.undo_btn.setCursor(Qt.PointingHandCursor)
        self.undo_btn.clicked.connect(self.undo_requested.emit)

        self.new_session_btn = QPushButton("Organize Another Directory")
        self.new_session_btn.setMinimumHeight(44)
        self.new_session_btn.setCursor(Qt.PointingHandCursor)
        self.new_session_btn.clicked.connect(self.organize_another_requested.emit)

        btn_layout.addWidget(self.open_dest_btn)
        btn_layout.addWidget(self.undo_btn)
        btn_layout.addWidget(self.new_session_btn)

        layout.addLayout(btn_layout)
        self.apply_shadows("dark")

    def apply_shadows(self, theme: str = "dark"):
        """Apply 3D elevation drop shadows to the statistics card."""
        apply_card_shadow(self.stats_card, theme)

    def _create_stat_widget(
        self, grid: QGridLayout, title: str, default_val: str, row: int, col: int, color: str
    ) -> QLabel:
        box = QVBoxLayout()
        box.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "card-desc")
        lbl_title.setStyleSheet("font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")

        lbl_val = QLabel(default_val)
        lbl_val.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color};")

        box.addWidget(lbl_title)
        box.addWidget(lbl_val)

        container = QWidget()
        container.setLayout(box)
        grid.addWidget(container, row, col)
        return lbl_val

    def populate(self, result: OperationResult):
        """Populate view with execution result data."""
        self.result = result

        if result.is_dry_run:
            self.icon_badge.setText("i")
            self.icon_badge.setStyleSheet(
                "font-size: 32px; font-weight: 800; color: #3b82f6; "
                "background-color: rgba(59, 130, 246, 0.12); border: 2px solid #3b82f6; "
                "border-radius: 36px; min-width: 72px; max-width: 72px; min-height: 72px; max-height: 72px;"
            )
            self.title_lbl.setText("Simulation Complete")
            self.title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #3b82f6;")
            self.subtitle_lbl.setText("Dry-run preview generated. No files on disk were modified.")
            self.undo_btn.setEnabled(False)
        else:
            self.icon_badge.setText("✓")
            self.icon_badge.setStyleSheet(
                "font-size: 32px; font-weight: 800; color: #10b981; "
                "background-color: rgba(16, 185, 129, 0.12); border: 2px solid #10b981; "
                "border-radius: 36px; min-width: 72px; max-width: 72px; min-height: 72px; max-height: 72px;"
            )
            self.title_lbl.setText("Organization Complete")
            self.title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #10b981;")
            self.subtitle_lbl.setText("All eligible files have been relocated into clean directory structures.")
            self.undo_btn.setEnabled(result.total_moved > 0)

        self.moved_val.setText(str(result.total_moved))
        self.skipped_val.setText(str(result.total_skipped))
        self.failed_val.setText(str(result.total_failed))
        self.duration_val.setText(f"{result.duration_seconds}s")

        self.dest_notice_lbl.setText(f"Target Directory: {result.destination_folder}")

    def _open_destination(self):
        if not self.result:
            return
        dest = self.result.destination_folder
        if not Path(dest).exists():
            QMessageBox.warning(self, "Directory Not Found", f"The path {dest} does not exist.")
            return

        try:
            if sys.platform == "win32":
                os.startfile(dest)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", dest])
            else:
                subprocess.Popen(["xdg-open", dest])
        except Exception as e:
            QMessageBox.warning(self, "Could Not Open Directory", str(e))
