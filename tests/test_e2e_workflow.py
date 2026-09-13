"""End-to-end headless workflow test executing complete scan -> organize -> undo sequence."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from src.models.organization_rule import OrganizationConfig, OrganizationMode
from src.core.scanner import FileScanner
from src.core.classifier import FileClassifier
from src.core.organizer import FileOrganizer
from src.core.undo_manager import UndoManager


class TestE2EWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name) / "Downloads"
        self.source_dir.mkdir()

        # Populate Downloads with test files
        (self.source_dir / "sunset.jpg").write_text("image content")
        (self.source_dir / "invoice.pdf").write_text("pdf document")
        (self.source_dir / "backup.zip").write_text("archive bytes")
        (self.source_dir / "run.py").write_text("print('hello')")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_juggle_and_undo_lifecycle(self):
        # 1. Configure
        config = OrganizationConfig(mode=OrganizationMode.BY_TYPE)
        scanner = FileScanner(config)
        classifier = FileClassifier(config)
        organizer = FileOrganizer(config)
        undo_manager = UndoManager()

        # 2. Scan
        items = scanner.scan(str(self.source_dir))
        self.assertEqual(len(items), 4)

        # 3. Classify (organize inside Downloads subfolders)
        classifier.classify_all(items, str(self.source_dir))

        categories = {i.name: i.category for i in items}
        self.assertEqual(categories["sunset.jpg"], "Photos & Images")
        self.assertEqual(categories["invoice.pdf"], "PDF Documents")
        self.assertEqual(categories["backup.zip"], "Archives")
        self.assertEqual(categories["run.py"], "Code")

        # 4. Organize
        result = organizer.organize(items, str(self.source_dir), str(self.source_dir))
        self.assertEqual(result.total_moved, 4)
        self.assertEqual(result.total_failed, 0)
        self.assertEqual(result.total_skipped, 0)

        # Verify destination files exist
        self.assertTrue((self.source_dir / "Photos & Images" / "sunset.jpg").exists())
        self.assertTrue((self.source_dir / "PDF Documents" / "invoice.pdf").exists())
        self.assertTrue((self.source_dir / "Archives" / "backup.zip").exists())
        self.assertTrue((self.source_dir / "Code" / "run.py").exists())

        # Verify original top-level files are moved
        self.assertFalse((self.source_dir / "sunset.jpg").exists())
        self.assertFalse((self.source_dir / "invoice.pdf").exists())

        # 5. Undo
        undo_manager.record_session(result)
        self.assertTrue(undo_manager.can_undo())

        restored, errors, _ = undo_manager.undo_last()
        self.assertEqual(restored, 4)
        self.assertEqual(errors, 0)

        # Verify files are restored back to top-level Downloads
        self.assertTrue((self.source_dir / "sunset.jpg").exists())
        self.assertTrue((self.source_dir / "invoice.pdf").exists())
        self.assertTrue((self.source_dir / "backup.zip").exists())
        self.assertTrue((self.source_dir / "run.py").exists())

        # Verify category folders are removed after emptying
        self.assertFalse((self.source_dir / "Photos & Images").exists())
        self.assertFalse((self.source_dir / "PDF Documents").exists())
        self.assertFalse((self.source_dir / "Archives").exists())
        self.assertFalse((self.source_dir / "Code").exists())

    def test_complete_juggle_and_disband_lifecycle(self):
        from src.services.history_service import HistoryService
        config_dir = Path(self.temp_dir.name) / "config"
        config_dir.mkdir()
        history_service = HistoryService(config_dir=config_dir)

        # 1. Configure & Scan
        config = OrganizationConfig(mode=OrganizationMode.BY_TYPE)
        scanner = FileScanner(config)
        classifier = FileClassifier(config)
        organizer = FileOrganizer(config)

        items = scanner.scan(str(self.source_dir))
        self.assertEqual(len(items), 4)
        classifier.classify_all(items, str(self.source_dir))

        # 2. Organize
        result = organizer.organize(items, str(self.source_dir), str(self.source_dir))
        self.assertEqual(result.total_moved, 4)

        # 3. Record in persistent history
        history_service.record_session(result)
        history = history_service.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "active")

        # 4. Disband from history
        restored, errors, msgs = history_service.disband_session(result.session_id)
        self.assertEqual(restored, 4)
        self.assertEqual(errors, 0)

        # 5. Verify files restored to source root
        self.assertTrue((self.source_dir / "sunset.jpg").exists())
        self.assertTrue((self.source_dir / "invoice.pdf").exists())
        self.assertTrue((self.source_dir / "backup.zip").exists())
        self.assertTrue((self.source_dir / "run.py").exists())

        # Verify created category folders pruned
        self.assertFalse((self.source_dir / "Photos & Images").exists())
        self.assertFalse((self.source_dir / "PDF Documents").exists())
        self.assertFalse((self.source_dir / "Archives").exists())
        self.assertFalse((self.source_dir / "Code").exists())

        # Verify status is now disbanded
        session = history_service.get_session(result.session_id)
        self.assertEqual(session["status"], "disbanded")


if __name__ == "__main__":
    unittest.main()
