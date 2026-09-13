"""Smoke tests for PySide6 UI views running with QOffscreenSurface."""
import os
import unittest
from PySide6.QtWidgets import QApplication

# Run Qt in offscreen / headless mode for automated testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure QApplication singleton
app = QApplication.instance() or QApplication([])

from src.models.file_item import FileItem
from src.models.operation_result import OperationResult
from src.ui.main_window import MainWindow
from src.ui.views.setup_view import SetupView
from src.ui.views.preview_view import PreviewView
from src.ui.views.results_view import ResultsView
from src.ui.dialogs.confirm_dialog import ConfirmDialog
from src.ui.dialogs.progress_dialog import ProgressDialog
from src.ui.dialogs.history_dialog import HistoryDialog
from src.services.history_service import HistoryService


class TestUISmoke(unittest.TestCase):

    def test_setup_view_init(self):
        view = SetupView()
        self.assertIsNotNone(view)
        self.assertTrue(view.preview_btn.isEnabled())

    def test_preview_view_population(self):
        view = PreviewView()
        items = [
            FileItem(name="pic.jpg", full_path="C:/mock/pic.jpg", extension=".jpg", size_bytes=1024, modified_time=0.0, category="Images", proposed_destination="C:/mock/dest/Images/pic.jpg"),
            FileItem(name="doc.pdf", full_path="C:/mock/doc.pdf", extension=".pdf", size_bytes=2048, modified_time=0.0, category="Documents", proposed_destination="C:/mock/dest/Documents/doc.pdf"),
        ]
        view.populate(items)
        self.assertEqual(view.table.rowCount(), 2)

    def test_results_view_population(self):
        view = ResultsView()
        result = OperationResult(
            session_id="test1",
            mode="file_type",
            source_folder="C:/mock/source",
            destination_folder="C:/mock/dest",
            total_scanned=5,
            total_moved=4,
            total_skipped=1,
            total_failed=0,
            duration_seconds=0.35,
        )
        view.populate(result)
        self.assertEqual(view.moved_val.text(), "4")
        self.assertEqual(view.skipped_val.text(), "1")

    def test_main_window_init(self):
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertEqual(window.stack.count(), 3)
        # Verify initial view is SetupView
        self.assertEqual(window.stack.currentIndex(), 0)

    def test_dialogs_init(self):
        confirm = ConfirmDialog(10, 5000, 3, False)
        self.assertIsNotNone(confirm)

        progress = ProgressDialog()
        progress.update_progress(5, 10, "test.txt", "Processing")
        self.assertEqual(progress.progress_bar.value(), 50)

        history_svc = HistoryService()
        history_dialog = HistoryDialog(history_svc)
        self.assertIsNotNone(history_dialog)


if __name__ == "__main__":
    unittest.main()
