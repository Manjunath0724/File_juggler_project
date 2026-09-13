"""Operation History dialog for browsing past file juggles and executing disband/rollback."""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from src.services.history_service import HistoryService
from src.ui.theme import apply_card_shadow


def _format_timestamp(iso_str: str) -> str:
    """Format an ISO timestamp into a human-readable corporate date and time."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y - %I:%M %p")
    except Exception:
        return iso_str


class SessionCard(QFrame):
    """Card widget representing a single historical juggle session."""

    disband_requested = Signal(str)  # session_id
    open_folder_requested = Signal(str)  # folder_path

    def __init__(self, session_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.session = session_data
        self.files_expanded = False
        self._init_ui()

    def _init_ui(self):
        self.setProperty("class", "card")
        self.setObjectName("sessionCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # 1. Top Row: Timestamp, Mode Badge, and Status Pill
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        time_str = _format_timestamp(self.session.get("timestamp", ""))
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("font-weight: 700; font-size: 14px;")

        mode_badge = QLabel(self.session.get("mode", "Standard"))
        mode_badge.setProperty("class", "badge")

        top_row.addWidget(time_lbl)
        top_row.addWidget(mode_badge)
        top_row.addStretch()

        # Status Pill
        status = self.session.get("status", "active")
        self.status_pill = QLabel()
        self._update_status_pill(status)
        top_row.addWidget(self.status_pill)

        layout.addLayout(top_row)

        # 2. Folder Paths Row
        paths_box = QVBoxLayout()
        paths_box.setSpacing(4)

        source_path = self.session.get("source_folder", "")
        dest_path = self.session.get("destination_folder", "")

        src_lbl = QLabel(f"Source: {source_path}")
        src_lbl.setProperty("class", "card-desc")
        src_lbl.setStyleSheet("font-size: 12px; font-family: 'Consolas', 'Courier New', monospace;")
        src_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        dest_lbl = QLabel(f"Destination: {dest_path}")
        dest_lbl.setProperty("class", "card-desc")
        dest_lbl.setStyleSheet("font-size: 12px; font-family: 'Consolas', 'Courier New', monospace;")
        dest_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        paths_box.addWidget(src_lbl)
        paths_box.addWidget(dest_lbl)
        layout.addLayout(paths_box)

        # 3. Metrics Row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        moved_cnt = self.session.get("total_moved", len(self.session.get("moves", [])))
        dur = self.session.get("duration_seconds", 0.0)

        stat_moved = QLabel(f"Files Moved: {moved_cnt}")
        stat_moved.setStyleSheet("font-weight: 600; color: #10b981;")

        stat_dur = QLabel(f"Duration: {dur}s")
        stat_dur.setProperty("class", "card-desc")

        metrics_row.addWidget(stat_moved)
        metrics_row.addWidget(stat_dur)
        metrics_row.addStretch()
        layout.addLayout(metrics_row)

        # 4. Optional Collapsible Files Table
        self.files_container = QWidget()
        self.files_container.setVisible(False)
        fc_layout = QVBoxLayout(self.files_container)
        fc_layout.setContentsMargins(0, 8, 0, 0)
        fc_layout.setSpacing(6)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Original File", "Category", "Relocated Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMaximumHeight(160)

        moves = self.session.get("moves", [])
        self.table.setRowCount(len(moves))
        for r, m in enumerate(moves):
            orig_name = m.get("original_name") or Path(m.get("source", "")).name
            cat = m.get("category", "")
            dest_p = m.get("destination", "")

            self.table.setItem(r, 0, QTableWidgetItem(orig_name))
            self.table.setItem(r, 1, QTableWidgetItem(cat))
            self.table.setItem(r, 2, QTableWidgetItem(dest_p))

        fc_layout.addWidget(self.table)
        layout.addWidget(self.files_container)

        # 5. Actions Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        # View Files Toggle
        self.toggle_files_btn = QPushButton(f"View Files ({len(moves)})")
        self.toggle_files_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_files_btn.clicked.connect(self._toggle_files)
        actions_row.addWidget(self.toggle_files_btn)

        # Open Destination Directory
        open_btn = QPushButton("Open Destination")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(lambda: self.open_folder_requested.emit(dest_path))
        actions_row.addWidget(open_btn)

        actions_row.addStretch()

        # Disband Button
        self.disband_btn = QPushButton()
        self.disband_btn.setCursor(Qt.PointingHandCursor)
        self.disband_btn.setMinimumHeight(34)
        self._update_disband_button(status)
        self.disband_btn.clicked.connect(
            lambda: self.disband_requested.emit(self.session.get("session_id", ""))
        )
        actions_row.addWidget(self.disband_btn)

        layout.addLayout(actions_row)

    def _update_status_pill(self, status: str):
        if status == "disbanded":
            self.status_pill.setText("[DISBANDED]")
            self.status_pill.setStyleSheet(
                "font-size: 11px; font-weight: 700; color: #64748b; "
                "background-color: rgba(100, 116, 139, 0.12); border: 1px solid #64748b; "
                "padding: 3px 8px; border-radius: 6px;"
            )
        else:
            self.status_pill.setText("[ACTIVE]")
            self.status_pill.setStyleSheet(
                "font-size: 11px; font-weight: 700; color: #10b981; "
                "background-color: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; "
                "padding: 3px 8px; border-radius: 6px;"
            )

    def _update_disband_button(self, status: str):
        if status == "disbanded":
            self.disband_btn.setText("Disbanded")
            self.disband_btn.setEnabled(False)
            self.disband_btn.setToolTip("This session has already been disbanded and restored.")
            self.disband_btn.setStyleSheet("")
        else:
            self.disband_btn.setText("Disband Juggle")
            self.disband_btn.setEnabled(True)
            self.disband_btn.setToolTip("Restore all moved files back to their original source directory.")
            self.disband_btn.setStyleSheet(
                "QPushButton { border-color: #f59e0b; color: #f59e0b; font-weight: 700; } "
                "QPushButton:hover { background-color: rgba(245, 158, 11, 0.12); }"
            )

    def _toggle_files(self):
        self.files_expanded = not self.files_expanded
        self.files_container.setVisible(self.files_expanded)
        moves_cnt = len(self.session.get("moves", []))
        self.toggle_files_btn.setText(
            f"Hide Files ({moves_cnt})" if self.files_expanded else f"View Files ({moves_cnt})"
        )

    def mark_disbanded(self):
        """Update UI representation when disbanded."""
        self.session["status"] = "disbanded"
        self._update_status_pill("disbanded")
        self._update_disband_button("disbanded")


class HistoryDialog(QDialog):
    """Modal dialog displaying past juggle operations with rollback/disband actions."""

    session_disbanded = Signal(str)

    def __init__(self, history_service: HistoryService, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.history_service = history_service
        self.theme = theme
        self.setWindowTitle("Operation History & Disband")
        self.setModal(True)
        self.resize(860, 640)
        self.setMinimumSize(740, 500)

        self.cards: List[SessionCard] = []
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header Bar
        header = QHBoxLayout()
        titles_box = QVBoxLayout()
        titles_box.setSpacing(4)

        title = QLabel("Operation History")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")

        subtitle = QLabel("Review past file juggle operations and disband folders back to original states.")
        subtitle.setProperty("class", "subtitle")

        titles_box.addWidget(title)
        titles_box.addWidget(subtitle)
        header.addLayout(titles_box)
        header.addStretch()

        # Clear History button
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._confirm_clear_history)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        # Status Summary Bar
        self.summary_card = QFrame()
        self.summary_card.setProperty("class", "card")
        summary_layout = QHBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(16, 10, 16, 10)
        summary_layout.setSpacing(20)

        self.total_lbl = QLabel("Total: 0")
        self.total_lbl.setStyleSheet("font-weight: 600;")

        self.active_lbl = QLabel("Active Juggles: 0")
        self.active_lbl.setStyleSheet("font-weight: 600; color: #10b981;")

        self.disbanded_lbl = QLabel("Disbanded: 0")
        self.disbanded_lbl.setStyleSheet("font-weight: 600; color: #64748b;")

        summary_layout.addWidget(self.total_lbl)
        summary_layout.addWidget(self.active_lbl)
        summary_layout.addWidget(self.disbanded_lbl)
        summary_layout.addStretch()

        layout.addWidget(self.summary_card)
        apply_card_shadow(self.summary_card, self.theme)

        # Scrollable Sessions Container
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 8, 0)
        self.cards_layout.setSpacing(14)
        self.cards_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll, stretch=1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "primary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _load_sessions(self):
        """Populate the scroll area with cards for each session."""
        # Clear existing
        self.cards.clear()
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        history = self.history_service.get_history()

        # Update summary counts
        total = len(history)
        active = sum(1 for h in history if h.get("status") == "active")
        disbanded = total - active

        self.total_lbl.setText(f"Total Operations: {total}")
        self.active_lbl.setText(f"Active Juggles: {active}")
        self.disbanded_lbl.setText(f"Disbanded: {disbanded}")
        self.clear_btn.setEnabled(total > 0)

        if not history:
            empty_frame = QFrame()
            empty_frame.setProperty("class", "card")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(40, 40, 40, 40)
            empty_layout.setAlignment(Qt.AlignCenter)

            e_title = QLabel("No Operation History")
            e_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #64748b;")
            e_desc = QLabel("Completed file juggle operations will automatically appear here.")
            e_desc.setProperty("class", "card-desc")

            empty_layout.addWidget(e_title, alignment=Qt.AlignCenter)
            empty_layout.addWidget(e_desc, alignment=Qt.AlignCenter)
            self.cards_layout.addWidget(empty_frame)
            apply_card_shadow(empty_frame, self.theme)
            return

        for session in history:
            card = SessionCard(session)
            card.disband_requested.connect(self._on_disband_requested)
            card.open_folder_requested.connect(self._on_open_folder)
            self.cards_layout.addWidget(card)
            self.cards.append(card)
            apply_card_shadow(card, self.theme)

    def _on_open_folder(self, path_str: str):
        if not path_str or not Path(path_str).exists():
            QMessageBox.warning(self, "Directory Not Found", f"Directory path does not exist:\n{path_str}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(path_str)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path_str])
            else:
                subprocess.Popen(["xdg-open", path_str])
        except Exception as e:
            QMessageBox.warning(self, "Could Not Open Folder", str(e))

    def _on_disband_requested(self, session_id: str):
        session = self.history_service.get_session(session_id)
        if not session:
            QMessageBox.warning(self, "Session Not Found", "Selected session could not be found.")
            return

        moved_cnt = session.get("total_moved", len(session.get("moves", [])))
        src = session.get("source_folder", "")
        dest = session.get("destination_folder", "")

        reply = QMessageBox.question(
            self,
            "Confirm Juggle Disband",
            f"Are you sure you want to disband this juggle operation?\n\n"
            f"Files to restore: {moved_cnt}\n"
            f"Source directory: {src}\n"
            f"Current directory: {dest}\n\n"
            f"All moved files will be relocated back to their original locations and empty destination folders will be pruned.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        restored, errors, msgs = self.history_service.disband_session(session_id)

        if errors > 0 and restored == 0:
            QMessageBox.critical(
                self,
                "Disband Failed",
                f"Failed to restore files:\n\n" + "\n".join(msgs[:6])
            )
        elif errors > 0:
            QMessageBox.warning(
                self,
                "Disband Partially Completed",
                f"Restored {restored} files with {errors} warnings:\n\n" + "\n".join(msgs[:5])
            )
        else:
            QMessageBox.information(
                self,
                "Disband Successful",
                f"Successfully disbanded juggle!\n{restored} files restored back to original location."
            )

        # Notify parent and reload UI
        self.session_disbanded.emit(session_id)
        self._load_sessions()

    def _confirm_clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear All History?",
            "Are you sure you want to clear your operation history log?\n\n"
            "Note: This only clears the history log entries. It will not delete or move any files on disk.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_service.clear_history()
            self._load_sessions()
