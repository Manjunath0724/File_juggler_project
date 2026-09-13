"""Main Application Window for File Juggler, coordinating views and background tasks."""
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QMessageBox, QApplication
)

from src.models.file_item import FileItem
from src.models.organization_rule import OrganizationConfig
from src.models.operation_result import OperationResult
from src.core.scanner import FileScanner
from src.core.classifier import FileClassifier
from src.core.organizer import FileOrganizer
from src.core.undo_manager import UndoManager
from src.services.settings_service import SettingsService
from src.services.history_service import HistoryService
from src.services.logging_service import setup_logger
from src.ui.theme import get_stylesheet, get_theme_palette
from src.ui.views.setup_view import SetupView
from src.ui.views.preview_view import PreviewView
from src.ui.views.results_view import ResultsView
from src.ui.dialogs.confirm_dialog import ConfirmDialog
from src.ui.dialogs.progress_dialog import ProgressDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.history_dialog import HistoryDialog


class ScanWorker(QObject):
    """Background worker for scanning and classifying files without blocking UI."""

    finished = Signal(list)  # List[FileItem]
    error = Signal(str)

    def __init__(self, config: OrganizationConfig, source_path: str, dest_path: str):
        super().__init__()
        self.config = config
        self.source_path = source_path
        self.dest_path = dest_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            scanner = FileScanner(self.config)
            items = scanner.scan(
                self.source_path,
                should_cancel=lambda: self._is_cancelled
            )
            if self._is_cancelled:
                return

            classifier = FileClassifier(self.config)
            classified = classifier.classify_all(items, self.dest_path)

            self.finished.emit(classified)
        except Exception as e:
            self.error.emit(str(e))


class OrganizeWorker(QObject):
    """Background worker for safely moving files."""

    progress = Signal(int, int, str, str)  # current, total, filename, status_msg
    finished = Signal(object)              # OperationResult
    error = Signal(str)

    def __init__(
        self,
        config: OrganizationConfig,
        items: List[FileItem],
        source_path: str,
        dest_path: str
    ):
        super().__init__()
        self.config = config
        self.items = items
        self.source_path = source_path
        self.dest_path = dest_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            organizer = FileOrganizer(self.config)
            result = organizer.organize(
                self.items,
                self.source_path,
                self.dest_path,
                progress_callback=lambda curr, tot, fn, msg: self.progress.emit(curr, tot, fn, msg),
                should_cancel=lambda: self._is_cancelled
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Primary application window managing view transitions and state."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Juggler")
        self.resize(1000, 720)
        self.setMinimumSize(850, 600)

        # Services
        self.logger = setup_logger()
        self.settings_service = SettingsService()
        self.history_service = HistoryService()
        self.undo_manager = UndoManager()

        self.current_theme = "dark"
        self.current_config: Optional[OrganizationConfig] = None
        self.current_source = ""
        self.current_dest = ""
        self.current_items: List[FileItem] = []

        # Thread handles
        self.scan_thread: Optional[QThread] = None
        self.scan_worker: Optional[ScanWorker] = None
        self.org_thread: Optional[QThread] = None
        self.org_worker: Optional[OrganizeWorker] = None

        self._init_ui()
        self._load_preferences()

    def _init_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked view manager
        self.stack = QStackedWidget()

        self.setup_view = SetupView()
        self.preview_view = PreviewView()
        self.results_view = ResultsView()

        self.stack.addWidget(self.setup_view)    # Index 0
        self.stack.addWidget(self.preview_view)  # Index 1
        self.stack.addWidget(self.results_view)  # Index 2

        layout.addWidget(self.stack)

        # Connect Signals
        self.setup_view.preview_requested.connect(self._start_scan)
        self.setup_view.open_settings_requested.connect(self._open_settings)
        self.setup_view.open_history_requested.connect(self._open_history)
        self.setup_view.toggle_theme_requested.connect(self._toggle_theme)

        self.preview_view.back_requested.connect(lambda: self.stack.setCurrentIndex(0))
        self.preview_view.confirm_requested.connect(self._prompt_confirmation)

        self.results_view.organize_another_requested.connect(lambda: self.stack.setCurrentIndex(0))
        self.results_view.undo_requested.connect(self._execute_undo)

    def _load_preferences(self):
        settings = self.settings_service.load()
        self.current_theme = settings.get("theme", "dark")
        self._apply_theme(self.current_theme)

        # Restore last used folders if existing
        last_source = settings.get("last_source_folder", "")
        if last_source:
            self.setup_view.source_input.setText(last_source)

        last_dest = settings.get("last_destination_folder", "")
        if last_dest and last_dest != last_source:
            self.setup_view.dest_custom_rb.setChecked(True)
            self.setup_view.dest_input.setText(last_dest)

    def _apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        app = QApplication.instance()
        if app:
            app.setPalette(get_theme_palette(theme_name))
            app.setStyleSheet(get_stylesheet(theme_name))
        if hasattr(self, "setup_view"):
            self.setup_view.update_theme_label(theme_name)
        if hasattr(self, "preview_view"):
            self.preview_view.apply_shadows(theme_name)
        if hasattr(self, "results_view"):
            self.results_view.apply_shadows(theme_name)

    def _toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme(new_theme)
        settings = self.settings_service.load()
        settings["theme"] = new_theme
        self.settings_service.save(settings)

    def _open_settings(self):
        dialog = SettingsDialog(self.settings_service, self)
        dialog.settings_saved.connect(lambda s: self._apply_theme(s.get("theme", "dark")))
        dialog.exec()

    def _open_history(self):
        dialog = HistoryDialog(self.history_service, self.current_theme, self)
        dialog.exec()

    def _start_scan(self, config: OrganizationConfig, source_path: str, dest_path: str):
        self.current_config = config
        self.current_source = source_path
        self.current_dest = dest_path

        # Save last used folders
        settings = self.settings_service.load()
        settings["last_source_folder"] = source_path
        settings["last_destination_folder"] = dest_path
        self.settings_service.save(settings)

        # Start background scan
        self.setup_view.preview_btn.setEnabled(False)
        self.setup_view.preview_btn.setText("Scanning Files...")

        self.scan_thread = QThread()
        self.scan_worker = ScanWorker(config, source_path, dest_path)
        self.scan_worker.moveToThread(self.scan_thread)

        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)

        self.scan_thread.start()

    def _on_scan_finished(self, items: List[FileItem]):
        self._cleanup_scan_thread()
        self.setup_view.preview_btn.setEnabled(True)
        self.setup_view.preview_btn.setText("Preview Files  →")

        if not items:
            QMessageBox.information(
                self,
                "No Files Found",
                "We couldn't find any files to organize in this folder with the current rules.\n\n"
                "Tip: Check your exclusion settings or select a different folder."
            )
            return

        self.current_items = items
        self.preview_view.populate(items)
        self.stack.setCurrentIndex(1)  # Preview view

    def _on_scan_error(self, err: str):
        self._cleanup_scan_thread()
        self.setup_view.preview_btn.setEnabled(True)
        self.setup_view.preview_btn.setText("Preview Files  →")
        QMessageBox.critical(self, "Scanning Error", f"Failed to scan directory:\n{err}")

    def _cleanup_scan_thread(self):
        if self.scan_thread:
            self.scan_thread.quit()
            self.scan_thread.wait()
            self.scan_thread = None
            self.scan_worker = None

    def _prompt_confirmation(self, selected_items: List[FileItem]):
        if not selected_items:
            return

        total_bytes = sum(i.size_bytes for i in selected_items)
        category_count = len({i.category for i in selected_items})
        is_dry_run = self.current_config.dry_run if self.current_config else False

        confirm = ConfirmDialog(
            len(selected_items), total_bytes, category_count, is_dry_run, self
        )
        if confirm.exec() == ConfirmDialog.Accepted:
            self._start_organizing(selected_items)

    def _start_organizing(self, selected_items: List[FileItem]):
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.show()

        self.org_thread = QThread()
        self.org_worker = OrganizeWorker(
            self.current_config, selected_items, self.current_source, self.current_dest
        )
        self.org_worker.moveToThread(self.org_thread)

        self.org_thread.started.connect(self.org_worker.run)
        self.org_worker.progress.connect(self.progress_dialog.update_progress)
        self.progress_dialog.cancel_requested.connect(self.org_worker.cancel)

        self.org_worker.finished.connect(self._on_organize_finished)
        self.org_worker.error.connect(self._on_organize_error)

        self.org_thread.start()

    def _on_organize_finished(self, result: OperationResult):
        self._cleanup_org_thread()
        self.progress_dialog.accept()

        # Log & record undo
        self.logger.info(
            f"Organized session {result.session_id}: moved {result.total_moved}, "
            f"skipped {result.total_skipped}, failed {result.total_failed}."
        )
        self.undo_manager.record_session(result)

        # Record non-dry-run operations in persistent history
        if not result.is_dry_run and result.total_moved > 0:
            self.history_service.record_session(result)

        self.results_view.populate(result)
        self.stack.setCurrentIndex(2)  # Results view

    def _on_organize_error(self, err: str):
        self._cleanup_org_thread()
        self.progress_dialog.reject()
        QMessageBox.critical(self, "Organization Error", f"An error occurred while moving files:\n{err}")

    def _cleanup_org_thread(self):
        if self.org_thread:
            self.org_thread.quit()
            self.org_thread.wait()
            self.org_thread = None
            self.org_worker = None

    def _execute_undo(self):
        if not self.undo_manager.can_undo():
            QMessageBox.information(self, "Nothing to Undo", "There are no recent operations to undo.")
            return

        reply = QMessageBox.question(
            self,
            "Undo Last Operation?",
            "Do you want to restore moved files back to their original locations?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            last_session = self.undo_manager.get_last_session()
            last_session_id = last_session.session_id if last_session else None

            restored, errs, msgs = self.undo_manager.undo_last()

            # Synchronize status with history service
            if last_session_id:
                self.history_service.mark_session_disbanded(last_session_id)

            if errs > 0:
                QMessageBox.warning(
                    self,
                    "Undo Completed with Warnings",
                    f"Restored {restored} files.\n{errs} errors encountered:\n" + "\n".join(msgs[:5])
                )
            else:
                QMessageBox.information(
                    self,
                    "Undo Successful",
                    f"Successfully restored {restored} files back to their original locations!"
                )
            self.stack.setCurrentIndex(0)
